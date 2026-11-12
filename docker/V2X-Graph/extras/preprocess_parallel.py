"""Parallel, resumable, memory-bounded replacement for `python preprocess.py` (V2X-Seq-TFD).

The output is identical to upstream: each scenario goes through the unmodified
`datasets.tfd_dataset.process_argoverse` + `utils.TemporalData` + `torch.save`. Only the
driver differs:
  * a process pool instead of one serial loop (upstream: ~3.5 s/scenario -> ~35 h total);
  * `maxtasksperchild` so each worker restarts periodically and cannot grow without bound
    (the serial upstream run was OOM-killed at 62 GB after ~870 scenarios);
  * atomic writes (tmp file + rename), so a killed run never leaves a truncated .pt;
  * resumable: scenarios whose .pt already exists are skipped (same rule as upstream).

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


def _init():
    global _dm
    from dair_map_api import DAIRV2XMap
    torch.set_num_threads(1)
    _dm = DAIRV2XMap()


def _one(job):
    split, raw_path, road_path, asso_path, out_path, radius = job
    from datasets.tfd_dataset import process_argoverse
    from utils import TemporalData
    t0 = time.time()
    kwargs = process_argoverse(split, raw_path, _dm, radius, road_path, asso_path)
    data = TemporalData(**kwargs)
    tmp = out_path + '.tmp'
    torch.save(data, tmp)
    os.replace(tmp, out_path)
    return os.path.basename(out_path), time.time() - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True, help='.../cooperative-vehicle-infrastructure')
    p.add_argument('--split', required=True, choices=['train', 'val'])
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--maxtasksperchild', type=int, default=50)
    p.add_argument('--limit', type=int, default=0, help='process only N scenarios (testing)')
    p.add_argument('--local_radius', type=float, default=50)
    a = p.parse_args()
    if os.environ.get('PYTHONHASHSEED') is None:
        print('[warn] PYTHONHASHSEED unset: lane order in the .pt files will not be reproducible', flush=True)

    raw_dir = os.path.join(a.root, 'v2x_fusion', a.split, 'data')
    road_dir = os.path.join(a.root, 'infrastructure-trajectories', a.split, 'data')
    asso_dir = os.path.join(a.root, 'traj_match_labels', a.split, 'data')
    out_dir = os.path.join(a.root, 'v2x_fusion', a.split, 'processed')
    os.makedirs(out_dir, exist_ok=True)

    for f in os.listdir(out_dir):  # leftovers of a killed run
        if f.endswith('.tmp'):
            os.remove(os.path.join(out_dir, f))
    done = set(os.listdir(out_dir))
    todo = sorted(f for f in os.listdir(raw_dir) if os.path.splitext(f)[0] + '.pt' not in done)
    if a.limit:
        todo = todo[:a.limit]
    jobs = [(a.split, os.path.join(raw_dir, f), os.path.join(road_dir, f), os.path.join(asso_dir, f),
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
