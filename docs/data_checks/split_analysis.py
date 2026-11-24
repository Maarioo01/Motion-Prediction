"""How were the official train/val splits drawn? Reads only the first data row of each scenario.

Mounts: /data/tfd (V2X-Seq-TFD root, ro), /data/traj (V2X-Traj root, ro), /w (scratchpad).
For each scenario: id (file name), start timestamp, intersection. Then per split: dates,
intersections, id ranges; and for every val scenario the nearest train scenario at the same
intersection (time gap between clip starts). Writes /w/split_stats.json.
"""
import bisect, collections, datetime as dt, glob, json, os

SETS = {
    'tfd': ('/data/tfd/cooperative-vehicle-infrastructure/vehicle-trajectories/{s}', 9.9),
    'traj': ('/data/traj/ego-trajectories/{s}/data', 7.9),
}
TZ = dt.timezone(dt.timedelta(hours=8))  # Beijing


def first_row(path):
    with open(path) as f:
        header = f.readline().strip().split(',')
        row = f.readline().strip().split(',')
    r = dict(zip(header, row))
    return float(r['timestamp']), r['intersect_id']


out = {}
for name, (pat, dur) in SETS.items():
    rows = {}
    for split in ['train', 'val']:
        rows[split] = []
        for f in glob.glob(os.path.join(pat.format(s=split), '*.csv')):
            t, inter = first_row(f)
            rows[split].append((int(os.path.basename(f)[:-4]), t, inter))
    res = {}
    for split, r in rows.items():
        days = collections.Counter(dt.datetime.fromtimestamp(t, TZ).date().isoformat() for _, t, _ in r)
        hours = collections.Counter(dt.datetime.fromtimestamp(t, TZ).hour for _, t, _ in r)
        res[split] = {
            'n': len(r),
            'id_min': min(i for i, _, _ in r), 'id_max': max(i for i, _, _ in r),
            'first_day': min(days), 'last_day': max(days), 'n_days': len(days),
            'intersections': dict(collections.Counter(x for _, _, x in r).most_common()),
            'hours': dict(sorted(hours.items())),
            'days': dict(sorted(days.items())),
        }
    # shared days / intersections
    res['days_only_in_val'] = sorted(set(res['val']['days']) - set(res['train']['days']))
    res['days_only_in_train'] = len(set(res['train']['days']) - set(res['val']['days']))
    res['intersections_only_in_val'] = sorted(set(res['val']['intersections']) - set(res['train']['intersections']))
    res['intersections_only_in_train'] = sorted(set(res['train']['intersections']) - set(res['val']['intersections']))
    # nearest train clip at the same intersection for each val clip
    by_inter = collections.defaultdict(list)
    for _, t, x in rows['train']:
        by_inter[x].append(t)
    for v in by_inter.values():
        v.sort()
    gaps = []
    for _, t, x in rows['val']:
        ts = by_inter.get(x, [])
        if not ts:
            gaps.append(float('inf'))
            continue
        k = bisect.bisect_left(ts, t)
        cand = [abs(ts[j] - t) for j in (k - 1, k) if 0 <= j < len(ts)]
        gaps.append(min(cand))
    n = len(gaps)
    res['val_nearest_train_gap'] = {
        'overlapping_clip(<%.1fs)' % dur: sum(g < dur for g in gaps) / n,
        '<30s': sum(g < 30 for g in gaps) / n,
        '<60s': sum(g < 60 for g in gaps) / n,
        '<10min': sum(g < 600 for g in gaps) / n,
        'median_s': sorted(gaps)[n // 2],
    }
    # same check inside train (train clip vs nearest other train clip), for reference
    tg = []
    for x, ts in by_inter.items():
        for j in range(len(ts)):
            c = [abs(ts[j] - ts[i]) for i in (j - 1, j + 1) if 0 <= i < len(ts)]
            if c:
                tg.append(min(c))
    m = len(tg)
    res['train_nearest_train_gap'] = {
        'overlapping_clip(<%.1fs)' % dur: sum(g < dur for g in tg) / m,
        '<60s': sum(g < 60 for g in tg) / m, 'median_s': sorted(tg)[m // 2],
    }
    # does the scenario id carry time order? correlation of id with start time
    allr = sorted(rows['train'] + rows['val'], key=lambda r: r[0])
    inv = sum(1 for a, b in zip(allr, allr[1:]) if b[1] < a[1])
    res['id_time_inversions_frac'] = inv / max(1, len(allr) - 1)
    out[name] = res
    print(name, {s: res[s]['n'] for s in ['train', 'val']}, res['val_nearest_train_gap'], flush=True)

json.dump(out, open('/w/split_stats.json', 'w'), indent=1, default=str)
print('done')
