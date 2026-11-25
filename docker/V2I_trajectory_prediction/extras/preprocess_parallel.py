"""Parallel, resumable replacement for V2INet's serial `V2XDataset.process()` (V2X-Seq-TFD).

The output is what upstream writes: each scenario goes through the unmodified
`datasets.v2x_dataset.process_argoverse` + `datasets.v2x_dataset.TemporalData` + `torch.save`,
under the same file name (`<seq_id>.pt` in `<root>/<split>/v2x_processed/`). Only the driver differs:
  * a process pool instead of one serial loop (upstream: ~2-3 scenarios/s, ~4-5 h for TFD);
  * `maxtasksperchild` so workers restart periodically;
  * atomic writes (tmp file + rename), so a killed run never leaves a truncated .pt;
  * resumable: scenarios whose .pt already exists are skipped (same rule as upstream).
Like upstream, a scenario is skipped if its roadside CSV is missing (none are, on TFD).

Determinism: upstream gathers map lane ids in a Python set, so lane order in each .pt depends on
PYTHONHASHSEED (same values, permuted). Launch with PYTHONHASHSEED=0.

Run inside the v2inet-cu128 container, from /workspace (the V2INet repo root):
  PYTHONHASHSEED=0 python preprocess_parallel.py \
      --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure/vehicle-trajectories \
      --split val --workers 8
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, os.getcwd())  # upstream repo root (/workspace)

import torch  # noqa: E402

_dm = None


def _init():
    global _dm
    from datasets.dair_map_api import DAIRV2XMap
    torch.set_num_threads(1)
    _dm = DAIRV2XMap()


def _one(job):
    split, car_path, road_path, out_path, radius = job
    from datasets.v2x_dataset import process_argoverse, TemporalData
    t0 = time.time()
    kwargs = process_argoverse(_dm, split, car_path, radius, road_path=road_path)
    data = TemporalData(**kwargs)
    tmp = out_path + '.tmp'
    torch.save(data, tmp)
    os.replace(tmp, out_path)
    return os.path.basename(out_path), time.time() - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True, help='.../cooperative-vehicle-infrastructure/vehicle-trajectories')
    p.add_argument('--split', required=True, choices=['train', 'val'])
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--maxtasksperchild', type=int, default=50)
    p.add_argument('--limit', type=int, default=0, help='process only N scenarios (testing)')
    p.add_argument('--local_radius', type=float, default=50)
    a = p.parse_args()
    if os.environ.get('PYTHONHASHSEED') is None:
        print('[warn] PYTHONHASHSEED unset: lane order in the .pt files will not be reproducible', flush=True)

    # Same directories as upstream V2XDataset (raw_dir, road_raw_dir, processed_dir).
    raw_dir = os.path.join(a.root, a.split)
    road_dir = os.path.join(Path(a.root).parent, 'infrastructure-trajectories', a.split)
    out_dir = os.path.join(a.root, a.split, 'v2x_processed')
    os.makedirs(out_dir, exist_ok=True)

    for f in os.listdir(out_dir):  # leftovers of a killed run
        if f.endswith('.tmp'):
            os.remove(os.path.join(out_dir, f))
    done = set(os.listdir(out_dir))
    raw = sorted(x for x in os.listdir(raw_dir) if 'csv' in x)  # upstream's filter
    todo = [f for f in raw if os.path.splitext(f)[0] + '.pt' not in done]
    missing_road = [f for f in todo if not os.path.exists(os.path.join(road_dir, f))]
    todo = [f for f in todo if f not in set(missing_road)]
    if a.limit:
        todo = todo[:a.limit]
    jobs = [(a.split, os.path.join(raw_dir, f), os.path.join(road_dir, f),
             os.path.join(out_dir, os.path.splitext(f)[0] + '.pt'), a.local_radius) for f in todo]
    print(f'[{a.split}] {len(raw)} scenarios, {len(done)} done, {len(jobs)} to do, '
          f'{len(missing_road)} without roadside CSV (skipped), {a.workers} workers', flush=True)

    t0, n = time.time(), 0
    with Pool(a.workers, initializer=_init, maxtasksperchild=a.maxtasksperchild) as pool:
        for name, dt in pool.imap_unordered(_one, jobs, chunksize=1):
            n += 1
            if n % 200 == 0 or n == len(jobs):
                el = time.time() - t0
                print(f'[{a.split}] {n}/{len(jobs)}  {n / el:.2f} scen/s  '
                      f'eta {(len(jobs) - n) / (n / el) / 60:.0f} min', flush=True)
    print(f'[{a.split}] finished in {(time.time() - t0) / 60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
