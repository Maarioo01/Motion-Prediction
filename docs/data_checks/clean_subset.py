"""Leakage-free view of V2X-Seq-TFD val: val scenarios with no train clip close in time.

A val clip is "clean" if no train clip at the same intersection starts within GAP seconds
of it (default 60 s; a clip is 9.9 s long, so 60 s also excludes clips of the same approach
to the intersection). The stricter variant ignores the intersection: no train clip anywhere
within GAP seconds. Reads only the first row of each scenario.

Mounts: /data/tfd (V2X-Seq-TFD root, ro), /w (output dir). Writes:
  /w/tfd_val_clean<GAP>s.txt         scenario ids, one per line (same-intersection rule)
  /w/tfd_val_clean<GAP>s_strict.txt  scenario ids (any-intersection rule)
"""
import bisect, glob, os, sys

GAP = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
VEH = '/data/tfd/cooperative-vehicle-infrastructure/vehicle-trajectories/{}'


def first_row(path):
    with open(path) as f:
        h = f.readline().strip().split(',')
        r = dict(zip(h, f.readline().strip().split(',')))
    return float(r['timestamp']), r['intersect_id']


rows = {}
for split in ('train', 'val'):
    rows[split] = [(os.path.basename(f)[:-4], *first_row(f)) for f in glob.glob(os.path.join(VEH.format(split), '*.csv'))]

by_inter, all_t = {}, sorted(t for _, t, _ in rows['train'])
for _, t, x in rows['train']:
    by_inter.setdefault(x, []).append(t)
for v in by_inter.values():
    v.sort()


def min_gap(ts, t):
    k = bisect.bisect_left(ts, t)
    return min([abs(ts[j] - t) for j in (k - 1, k) if 0 <= j < len(ts)] or [float('inf')])


clean, strict = [], []
for sid, t, x in rows['val']:
    if min_gap(by_inter.get(x, []), t) >= GAP:
        clean.append(sid)
    if min_gap(all_t, t) >= GAP:
        strict.append(sid)
tag = f'{GAP:g}s'
for name, ids in ((f'tfd_val_clean{tag}.txt', clean), (f'tfd_val_clean{tag}_strict.txt', strict)):
    open(os.path.join('/w', name), 'w').write('\n'.join(sorted(ids, key=int)) + '\n')
n = len(rows['val'])
print(f'val {n}: clean (same intersection, gap >= {tag}) {len(clean)} ({100 * len(clean) / n:.1f} %), '
      f'strict (any intersection) {len(strict)} ({100 * len(strict) / n:.1f} %)')
