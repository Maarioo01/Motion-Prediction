# Inference + evaluation for one or more QCNet checkpoints on the Argoverse 2 validation split.
#
# Not part of upstream QCNet - added by this benchmark project (copied into the repo by setup.sh).
# Upstream val.py only prints aggregate metrics and assumes the default <root>/val/{raw,processed}
# layout; this script works with explicit raw/processed dirs and additionally writes:
#   - per-scenario metrics (CSV) for every checkpoint, using the exact same formulas as
#     QCNet's own metrics/ (minADE/minFDE/MR/Brier over the focal agent, K=6 and K=1),
#   - full predictions in world coordinates (NPZ, one per checkpoint),
#   - trajectory plots comparing all checkpoints side by side on the same scenarios.
#
# Example (inside the qcnet container):
#   python qcnet_inference.py \
#       --ckpt ours=lightning_logs/version_1/checkpoints/epoch=63-step=6397056.ckpt \
#       --ckpt official=QCNet_AV2.ckpt \
#       --raw_dir /data/argoverse2/val --processed_dir /workspace/data_staging/val_processed \
#       --out_dir /outputs
import argparse
import csv
import json
import random
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Subset
from torch_geometric.data import Batch
from torch_geometric.loader import DataLoader
from av2.map.map_api import ArgoverseStaticMap

from datasets import ArgoverseV2Dataset
from predictors import QCNet
from transforms import TargetBuilder

MISS_THRESHOLD = 2.0  # metres, same as QCNet's MR metric and the AV2 benchmark
METRIC_KEYS = ('minADE6', 'minFDE6', 'MR6', 'brier', 'brier_minFDE6', 'minADE1', 'minFDE1', 'MR1')

# Colors: reference categorical slots 1-3 (validated all-pairs) + neutral chrome.
SURFACE = '#fcfcfb'
INK_PRIMARY = '#0b0b0b'
INK_SECONDARY = '#52514e'
INK_MUTED = '#898781'
LANE = '#c3c2b7'
CROSSWALK = '#f0efec'
HISTORY = '#2a78d6'       # blue - observed past of the focal agent
PREDICTION = '#eb6834'    # orange - predicted modes
GROUND_TRUTH = '#1baf7a'  # aqua - real future (also dashed + labeled: sub-3:1 contrast)

# Published validation numbers from the QCNet README (Argoverse 2, val split).
PAPER_VAL = {'minADE6': 0.72, 'minFDE6': 1.25, 'MR6': 0.16, 'minADE1': 1.69, 'minFDE1': 4.32, 'MR1': 0.58,
             'brier_minFDE6': 1.87}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ckpt', action='append', required=True,
                        help='name=path/to/checkpoint.ckpt, repeatable; the first one drives best/worst selection')
    parser.add_argument('--root', type=str, default='/data/argoverse2')
    parser.add_argument('--raw_dir', type=str, required=True)
    parser.add_argument('--processed_dir', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--num_workers', type=int, default=8)
    parser.add_argument('--num_random_plots', type=int, default=30)
    parser.add_argument('--num_extreme_plots', type=int, default=5)
    parser.add_argument('--max_scenarios', type=int, default=None, help='evaluate only the first N (smoke test)')
    parser.add_argument('--seed', type=int, default=0)
    return parser.parse_args()


def local_to_world(traj, origin, theta):
    """traj [N, ..., 2] in each agent's frame at the last observed step -> city frame (as in QCNet.test_step)."""
    cos, sin = theta.cos(), theta.sin()
    rot = torch.stack([torch.stack([cos, sin], -1), torch.stack([-sin, cos], -1)], -2)  # [N, 2, 2]
    shape = traj.shape
    flat = traj.reshape(shape[0], -1, 2)
    return (torch.bmm(flat, rot) + origin.unsqueeze(1)).reshape(shape)


@torch.no_grad()
def run_model(model, data):
    """Returns focal-agent outputs: local + world trajectories [B, K, T, 2], probs [B, K], local GT, valid mask."""
    if isinstance(data, Batch):
        data['agent']['av_index'] += data['agent']['ptr'][:-1]
    pred = model(data)
    nh = model.num_historical_steps
    eval_mask = data['agent']['category'] == 3  # focal track, exactly one per scenario
    traj_local = pred['loc_refine_pos'][eval_mask, :, :, :2]
    prob = F.softmax(pred['pi'][eval_mask], dim=-1)
    gt_local = data['agent']['target'][eval_mask, :, :2]
    valid = data['agent']['predict_mask'][eval_mask, nh:]
    origin = data['agent']['position'][eval_mask, nh - 1, :2]
    theta = data['agent']['heading'][eval_mask, nh - 1]
    traj_world = local_to_world(traj_local, origin, theta)
    return traj_local, traj_world, prob, gt_local, valid


def focal_metrics(traj, prob, gt, valid):
    """Per-scenario metrics, mirroring QCNet's metrics/ (min_criterion='FDE', K = all 6 modes)."""
    b, _, t, _ = traj.shape
    v = valid.float()
    ar = torch.arange(b, device=traj.device)
    last = (v * torch.arange(1, t + 1, device=traj.device)).argmax(dim=-1)
    fde = torch.norm(traj[ar, :, last] - gt[ar, last].unsqueeze(1), dim=-1)  # [B, K]
    ade = (torch.norm(traj - gt.unsqueeze(1), dim=-1) * v.unsqueeze(1)).sum(-1) / v.sum(-1, keepdim=True)
    best = fde.argmin(dim=-1)
    top = prob.argmax(dim=-1)
    brier = (1.0 - prob[ar, best]).pow(2)
    return {
        'minADE6': ade[ar, best], 'minFDE6': fde[ar, best], 'MR6': (fde[ar, best] > MISS_THRESHOLD).float(),
        'brier': brier, 'brier_minFDE6': fde[ar, best] + brier,
        'minADE1': ade[ar, top], 'minFDE1': fde[ar, top], 'MR1': (fde[ar, top] > MISS_THRESHOLD).float(),
        'best_mode': best.float(), 'top_mode': top.float(), 'p_top': prob[ar, top],
    }


def evaluate(name, model, dataset, args, device, out_dir):
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers,
                        pin_memory=True)
    rows, trajs, probs, ids = [], [], [], []
    start = time.time()
    for i, data in enumerate(loader):
        data = data.to(device)
        traj_local, traj_world, prob, gt_local, valid = run_model(model, data)
        m = focal_metrics(traj_local, prob, gt_local, valid)
        for j, sid in enumerate(data['scenario_id']):
            row = {'scenario_id': sid, 'city': data['city'][j]}
            row.update({k: float(v[j]) for k, v in m.items()})
            rows.append(row)
        trajs.append(traj_world.cpu().numpy().astype(np.float32))
        probs.append(prob.cpu().numpy().astype(np.float32))
        ids.extend(data['scenario_id'])
        if i % 250 == 0:
            rate = len(rows) / max(time.time() - start, 1e-6)
            print(f'[{name}] {len(rows)}/{len(dataset)} scenarios, {rate:.1f} scen/s', flush=True)

    summary = {k: float(np.mean([r[k] for r in rows])) for k in METRIC_KEYS}
    summary['num_scenarios'] = len(rows)
    with open(out_dir / f'per_scenario_metrics_{name}.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(out_dir / f'predictions_{name}.npz', scenario_id=np.array(ids),
                        trajectories_world=np.concatenate(trajs), probabilities=np.concatenate(probs))
    print(f'[{name}] done in {(time.time() - start) / 60:.1f} min: {json.dumps(summary)}', flush=True)
    return rows, summary


def draw_map(ax, raw_dir, scenario_id, extent):
    """Lane boundaries and crosswalks from the raw AV2 map, clipped to the plot window."""
    map_dir = Path(raw_dir) / scenario_id
    map_path = sorted(map_dir.glob('log_map_archive_*.json'))[0]
    avm = ArgoverseStaticMap.from_json(map_path)
    (x0, x1), (y0, y1) = extent
    for crossing in avm.vector_pedestrian_crossings.values():
        poly = crossing.polygon[:, :2]
        ax.fill(poly[:, 0], poly[:, 1], color=CROSSWALK, zorder=0, linewidth=0)
    for lane in avm.vector_lane_segments.values():
        for boundary in (lane.left_lane_boundary.xyz, lane.right_lane_boundary.xyz):
            xy = boundary[:, :2]
            if (xy[:, 0].max() < x0 or xy[:, 0].min() > x1 or xy[:, 1].max() < y0 or xy[:, 1].min() > y1):
                continue
            ax.plot(xy[:, 0], xy[:, 1], color=LANE, linewidth=0.8, zorder=1, solid_capstyle='round')


def plot_scenario(scenario_idx, dataset, models, raw_dir, out_path, tag):
    data = Batch.from_data_list([dataset[scenario_idx]])
    nh = next(iter(models.values())).num_historical_steps
    sid = data['scenario_id'][0]
    city = data['city'][0]
    pos = data['agent']['position'][:, :, :2]
    valid = data['agent']['valid_mask']
    focal = int((data['agent']['category'] == 3).nonzero()[0])
    av = int(data['agent']['av_index'][0])
    hist = pos[focal, :nh][valid[focal, :nh]].numpy()
    future_mask = data['agent']['predict_mask'][focal, nh:]
    gt = pos[focal, nh:][future_mask].numpy()

    outputs = {}
    for name, model in models.items():
        device = next(model.parameters()).device
        batch = Batch.from_data_list([dataset[scenario_idx]]).to(device)
        traj_local, traj_world, prob, gt_local, vmask = run_model(model, batch)
        m = focal_metrics(traj_local, prob, gt_local, vmask)
        outputs[name] = (traj_world[0].cpu().numpy(), prob[0].cpu().numpy(), {k: float(v[0]) for k, v in m.items()})

    # Shared square window around everything the focal agent did or might do.
    pts = [hist, gt] + [o[0].reshape(-1, 2) for o in outputs.values()]
    pts = np.concatenate([p for p in pts if len(p)])
    cx, cy = (pts.min(0) + pts.max(0)) / 2
    half = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1])) / 2 + 8.0
    extent = ((cx - half, cx + half), (cy - half, cy + half))

    fig, axes = plt.subplots(1, len(models), figsize=(6.4 * len(models), 6.9), facecolor=SURFACE)
    axes = np.atleast_1d(axes)
    for ax, (name, (traj, prob, m)) in zip(axes, outputs.items()):
        ax.set_facecolor(SURFACE)
        draw_map(ax, raw_dir, sid, extent)
        # Other agents: observed past in muted ink, current position as a dot.
        for a in range(pos.size(0)):
            if a == focal or not valid[a, :nh].any():
                continue
            p = pos[a, :nh][valid[a, :nh]].numpy()
            ax.plot(p[:, 0], p[:, 1], color=INK_MUTED, linewidth=1.0, alpha=0.6, zorder=2)
            if valid[a, nh - 1]:
                ax.scatter(*pos[a, nh - 1].numpy(), s=14, color=INK_MUTED, zorder=3, linewidths=0)
        if valid[av, nh - 1]:
            ax.scatter(*pos[av, nh - 1].numpy(), s=60, marker='s', color=INK_SECONDARY, zorder=4,
                       edgecolors=SURFACE, linewidths=1.5)
            ax.annotate('AV', pos[av, nh - 1].numpy(), xytext=(5, 5), textcoords='offset points',
                        color=INK_SECONDARY, fontsize=8, zorder=8)
        # Predicted modes: line width / opacity scale with probability, probability labelled at the endpoint.
        order = np.argsort(prob)
        labelled = set(order[-3:])  # direct-label only the 3 most likely modes to avoid endpoint pile-ups
        for k in order:
            w = 1.2 + 3.0 * prob[k]
            ax.plot(traj[k, :, 0], traj[k, :, 1], color=PREDICTION, linewidth=w, alpha=0.45 + 0.55 * prob[k] /
                    prob.max(), zorder=5, solid_capstyle='round')
            ax.scatter(*traj[k, -1], s=22, color=PREDICTION, zorder=6, edgecolors=SURFACE, linewidths=1.2)
            if k in labelled:
                ax.annotate(f'{prob[k]:.2f}', traj[k, -1], xytext=(4, -10), textcoords='offset points',
                            color=INK_SECONDARY, fontsize=7.5, zorder=8)
        ax.plot(hist[:, 0], hist[:, 1], color=HISTORY, linewidth=2.5, zorder=6, solid_capstyle='round')
        ax.scatter(*hist[-1], s=70, color=HISTORY, zorder=7, edgecolors=SURFACE, linewidths=1.8)
        if len(gt):
            ax.plot(gt[:, 0], gt[:, 1], color=GROUND_TRUTH, linewidth=2.5, linestyle=(0, (4, 2)), zorder=7)
            ax.scatter(*gt[-1], s=90, marker='*', color=GROUND_TRUTH, zorder=8, edgecolors=INK_PRIMARY,
                       linewidths=0.6)
            ax.annotate('GT', gt[-1], xytext=(5, 4), textcoords='offset points', color=INK_PRIMARY,
                        fontsize=8, fontweight='bold', zorder=9)
        ax.set_xlim(*extent[0])
        ax.set_ylim(*extent[1])
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(LANE)
        miss = 'MISS' if m['MR6'] > 0.5 else 'hit'
        ax.set_title(f'{name}\nminADE6 {m["minADE6"]:.2f} m · minFDE6 {m["minFDE6"]:.2f} m ({miss}) · '
                     f'top-1 FDE {m["minFDE1"]:.2f} m', fontsize=9.5, color=INK_PRIMARY, loc='left')

    legend = [Line2D([0], [0], color=HISTORY, lw=2.5, label='Focal agent - observed 5 s'),
              Line2D([0], [0], color=GROUND_TRUTH, lw=2.5, ls=(0, (4, 2)), label='Ground truth - next 6 s'),
              Line2D([0], [0], color=PREDICTION, lw=2.5, label='6 predicted modes (top-3 labelled with probability)'),
              Line2D([0], [0], color=INK_MUTED, lw=1.0, marker='o', ms=4, label='Other agents (past)'),
              Line2D([0], [0], color=INK_SECONDARY, lw=0, marker='s', ms=7, label='Autonomous vehicle')]
    fig.legend(handles=legend, loc='lower center', ncol=len(legend), frameon=False, fontsize=8.5,
               labelcolor=INK_SECONDARY)
    fig.suptitle(f'[{tag}] scenario {sid} · {city}', fontsize=11, color=INK_PRIMARY, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    fig.savefig(out_path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    out_dir = Path(args.out_dir)
    (out_dir / 'plots').mkdir(parents=True, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    models = {}
    for spec in args.ckpt:
        name, path = spec.split('=', 1)
        models[name] = QCNet.load_from_checkpoint(checkpoint_path=path, map_location=device).eval().to(device)
        print(f'loaded {name} <- {path}', flush=True)

    first = next(iter(models.values()))
    dataset = ArgoverseV2Dataset(args.root, 'val', raw_dir=args.raw_dir, processed_dir=args.processed_dir,
                                 transform=TargetBuilder(first.num_historical_steps, first.num_future_steps))
    if args.max_scenarios:
        dataset = Subset(dataset, range(min(args.max_scenarios, len(dataset))))
    print(f'validation scenarios: {len(dataset)}', flush=True)

    results, summaries = {}, {}
    for name, model in models.items():
        results[name], summaries[name] = evaluate(name, model, dataset, args, device, out_dir)
    with open(out_dir / 'metrics_summary.json', 'w') as f:
        json.dump({'paper_val': PAPER_VAL, **summaries, 'checkpoints': dict(s.split('=', 1) for s in args.ckpt)},
                  f, indent=2)

    # Scenario selection: a fixed random sample, plus the best and worst cases of the first checkpoint.
    rng = random.Random(args.seed)
    n = len(dataset)
    selections = {'random': rng.sample(range(n), min(args.num_random_plots, n))}
    ranked = sorted(range(n), key=lambda i: results[next(iter(models))][i]['minFDE6'])
    selections['best'] = ranked[:args.num_extreme_plots]
    selections['worst'] = ranked[-args.num_extreme_plots:][::-1]
    for tag, indices in selections.items():
        (out_dir / 'plots' / tag).mkdir(exist_ok=True)
        for rank, idx in enumerate(indices):
            sid = results[next(iter(models))][idx]['scenario_id']
            plot_scenario(idx, dataset, models, args.raw_dir, out_dir / 'plots' / tag / f'{rank:02d}_{sid}.png', tag)
        print(f'plots/{tag}: {len(indices)} figures', flush=True)
    print('INFERENCE_DONE', flush=True)


if __name__ == '__main__':
    main()
