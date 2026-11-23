"""Parallel, resumable, memory-bounded replacement for `python preprocess.py` (V2X-Seq-TFD, V2X-Traj).

The output is identical to upstream: each scenario goes through the unmodified
`datasets.{tfd,v2x_traj}_dataset.process_argoverse` + `utils.TemporalData` + `torch.save`. Only the
driver differs:
  * a process pool instead of one serial loop (upstream: ~3.5 s/scenario -> ~35 h total);
  * `maxtasksperchild` so each worker restarts periodically and cannot grow without bound
    (the serial upstream run was OOM-killed at 62 GB after ~870 scenarios);
  * atomic writes (tmp file + rename), so a killed run never leaves a truncated .pt;
  * resumable: scenarios whose .pt already exists are skipped (same rule as upstream).

Memory fix (output-identical): upstream `utils.rowwise_in(a, b)` tests which rows of `a`
(all agent-pair edges, ~N^2) occur in `b` (V2X pairs) by broadcasting an |a| x |b| x 2
tensor. Crowded scenes need >100 GB (one val scenario asked for 128 GB). It is replaced,
in the dataset modules only, by `rowwise_in_isin`: each (i, j) row becomes one int64 key
and `torch.isin` does the lookup. Same boolean mask; checked against the original on
random inputs (`--selftest`) and on already-written .pt files.

Determinism: upstream gathers map lane ids (strings) in a Python set, so lane order in
each .pt depends on PYTHONHASHSEED (values are identical, only permuted). Launch with
PYTHONHASHSEED=0 for byte-reproducible caches; the driver warns otherwise.

Run inside the v2x-graph container, from /workspace:
  PYTHONHASHSEED=0 python preprocess_parallel.py --root <coop root> --split val --workers 6
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.getcwd())  # upstream repo root (/workspace)

import torch  # noqa: E402

_dm = None


def rowwise_in_isin(a, b):
    """Same result as upstream utils.rowwise_in for 2-column integer index tensors."""
    from utils import rowwise_in as _orig
    if a.dim() != 2 or b.dim() != 2 or a.shape[1] != 2 or b.shape[1] != 2 or a.is_floating_point():
        return _orig(a, b)
    if a.shape[0] == 0 or b.shape[0] == 0:
        return torch.zeros(a.shape[0], dtype=torch.bool)
    m = int(max(a.max(), b.max())) + 1
    lo = int(min(a.min(), b.min()))
    ka = (a[:, 0] - lo) * m + (a[:, 1] - lo)
    kb = (b[:, 0] - lo) * m + (b[:, 1] - lo)
    return torch.isin(ka, kb)


def _patch():
    import datasets.tfd_dataset as tfd
    import datasets.v2x_traj_dataset as v2xt
    tfd.rowwise_in = rowwise_in_isin
    v2xt.rowwise_in = rowwise_in_isin


def selftest(n=2000):
    from utils import rowwise_in as orig
    g = torch.Generator().manual_seed(0)
    for t in range(n):
        na, nb, hi = [int(v) for v in torch.randint(0, 60, (3,), generator=g)]
        hi += 1
        a = torch.randint(0, hi, (na, 2), generator=g)
        b = torch.randint(0, hi, (nb, 2), generator=g)
        if t % 3 == 0 and na:
            b = torch.cat([b, a[: max(1, na // 2)]])  # guarantee hits
        assert torch.equal(orig(a, b), rowwise_in_isin(a, b)), (a, b)
    print(f'selftest ok: {n} random cases identical to upstream rowwise_in')


def _init():
    global _dm
    from dair_map_api import DAIRV2XMap
    torch.set_num_threads(1)
    _patch()
    _dm = DAIRV2XMap()


def _one(job):
    dataset, split, raw_path, extra_paths, out_path, radius = job
    if dataset == 'V2X-Seq-TFD':
        from datasets.tfd_dataset import process_argoverse
    else:
        from datasets.v2x_traj_dataset import process_argoverse
    from utils import TemporalData
    t0 = time.time()
    kwargs = process_argoverse(split, raw_path, _dm, radius, *extra_paths)
    data = TemporalData(**kwargs)
    tmp = out_path + '.tmp'
    torch.save(data, tmp)
    os.replace(tmp, out_path)
    return os.path.basename(out_path), time.time() - t0


# Directories, relative to --root, exactly as in the upstream Dataset classes.
# raw: the scenario list / ego view; extra: positional args after `radius`; out: processed.
LAYOUT = {
    'V2X-Seq-TFD': dict(raw='v2x_fusion', out='v2x_fusion',
                        extra=['infrastructure-trajectories', 'traj_match_labels']),
    'V2X-Traj': dict(raw='v2x_test', out='v2x_test',
                     extra=['infrastructure-trajectories', 'vehicle-trajectories', 'traj_match_labels']),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--selftest', action='store_true', help='check rowwise_in_isin and exit')
    p.add_argument('--root', required=False,
                   help='TFD: .../cooperative-vehicle-infrastructure; V2X-Traj: the v2x-traj root')
    p.add_argument('--dataset', default='V2X-Seq-TFD', choices=list(LAYOUT))
    p.add_argument('--split', choices=['train', 'val'])
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--maxtasksperchild', type=int, default=50)
    p.add_argument('--limit', type=int, default=0, help='process only N scenarios (testing)')
    p.add_argument('--local_radius', type=float, default=50)
    a = p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.root or not a.split:
        p.error('--root and --split are required')
    if os.environ.get('PYTHONHASHSEED') is None:
        print('[warn] PYTHONHASHSEED unset: lane order in the .pt files will not be reproducible', flush=True)

    lay = LAYOUT[a.dataset]
    raw_dir = os.path.join(a.root, lay['raw'], a.split, 'data')
    extra_dirs = [os.path.join(a.root, d, a.split, 'data') for d in lay['extra']]
    out_dir = os.path.join(a.root, lay['out'], a.split, 'processed')
    os.makedirs(out_dir, exist_ok=True)

    for f in os.listdir(out_dir):  # leftovers of a killed run
        if f.endswith('.tmp'):
            os.remove(os.path.join(out_dir, f))
    done = set(os.listdir(out_dir))
    todo = sorted(f for f in os.listdir(raw_dir) if os.path.splitext(f)[0] + '.pt' not in done)
    if a.limit:
        todo = todo[:a.limit]
    jobs = [(a.dataset, a.split, os.path.join(raw_dir, f), [os.path.join(d, f) for d in extra_dirs],
             os.path.join(out_dir, os.path.splitext(f)[0] + '.pt'), a.local_radius) for f in todo]
    print(f'[{a.split}] {len(done)} done, {len(jobs)} to do, {a.workers} workers', flush=True)

    t0, n = time.time(), 0
    with Pool(a.workers, initializer=_init, maxtasksperchild=a.maxtasksperchild) as pool:
        for name, dt in pool.imap_unordered(_one, jobs, chunksize=1):
            n += 1
            if n % 100 == 0 or n == len(jobs):
                el = time.time() - t0
                print(f'[{a.split}] {n}/{len(jobs)}  {n / el:.2f} scen/s  '
                      f'eta {(len(jobs) - n) / (n / el) / 3600:.1f} h', flush=True)
    print(f'[{a.split}] finished in {(time.time() - t0) / 3600:.2f} h', flush=True)


if __name__ == '__main__':
    main()
