"""Does a val scenario's target future appear inside a training scenario?

For each val scenario (all of V2X-Traj, a seeded sample of TFD), take the train scenarios at
the same intersection whose clip overlaps in time (start within one clip length). Count:
  same_av   : our car's positions agree (< 0.05 m) at shared timestamps -> same drive
  fut_in_tr : every future point of the val target (car-side file) has a row in the train
              file at the same timestamp within 0.05 m (any agent) -> the future was seen
              by training, possibly as another agent's supervised future
Mounts: /data/tfd, /data/traj (ro), /w (rw). Writes /w/leak_stats.json.
"""
import bisect, collections, glob, json, os, random, sys
import numpy as np
import pandas as pd

random.seed(0)
SETS = {
    'tfd': ('/data/tfd/cooperative-vehicle-infrastructure/vehicle-trajectories/{s}', 9.9, 5.0, 400),
    'traj': ('/data/traj/ego-trajectories/{s}/data', 7.9, 4.0, 400),
}


def first_row(path):
    with open(path) as f:
        h = f.readline().strip().split(',')
        r = dict(zip(h, f.readline().strip().split(',')))
    return float(r['timestamp']), r['intersect_id']


def load(path):
    df = pd.read_csv(path, usecols=['timestamp', 'id', 'tag', 'x', 'y'])
    df['tk'] = np.round(df.timestamp * 10).astype(np.int64)  # 0.1 s ticks
    return df


out = {}
for name, (pat, dur, hist, nval) in SETS.items():
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    train = collections.defaultdict(list)
    for f in glob.glob(os.path.join(pat.format(s='train'), '*.csv')):
        t, x = first_row(f)
        train[x].append((t, f))
    for v in train.values():
        v.sort()
    vals = sorted(glob.glob(os.path.join(pat.format(s='val'), '*.csv')))
    vals = random.sample(vals, min(nval, len(vals)))
    n = n_overlap = n_same_av = n_fut = n_fut_as_target = 0
    examples = []
    for vf in vals:
        t0, inter = first_row(vf)
        cands = [f for (t, f) in train.get(inter, []) if abs(t - t0) < dur]
        n += 1
        if not cands:
            continue
        n_overlap += 1
        v = load(vf)
        tgt = v[v.tag == 'TARGET_AGENT']
        t_obs = v.tk.min() + int(round(hist * 10)) - 1
        fut = tgt[tgt.tk > t_obs][['tk', 'x', 'y']].to_numpy()
        av_v = v[v.tag == 'AV'].set_index('tk')[['x', 'y']]
        same_av = seen = seen_tgt = False
        for tf in cands:
            tr = load(tf)
            av_t = tr[tr.tag == 'AV'].set_index('tk')[['x', 'y']]
            common = av_v.index.intersection(av_t.index)
            if len(common) and np.abs(av_v.loc[common].to_numpy() - av_t.loc[common].to_numpy()).max() < 0.05:
                same_av = True
            if len(fut):
                g = {k: d[['x', 'y']].to_numpy() for k, d in tr.groupby('tk')}
                ok = all(k in g and np.min(np.hypot(g[k][:, 0] - x, g[k][:, 1] - y)) < 0.05 for k, x, y in fut)
                if ok:
                    seen = True
                    # was it the train scenario's own target?
                    tt = tr[tr.tag == 'TARGET_AGENT']
                    gt = {k: d[['x', 'y']].to_numpy() for k, d in tt.groupby('tk')}
                    if all(k in gt and np.min(np.hypot(gt[k][:, 0] - x, gt[k][:, 1] - y)) < 0.05 for k, x, y in fut):
                        seen_tgt = True
                    if len(examples) < 3:
                        examples.append({'val': os.path.basename(vf), 'train': os.path.basename(tf),
                                         'start_gap_s': round(first_row(tf)[0] - t0, 1), 'future_points': len(fut)})
        n_same_av += same_av
        n_fut += seen
        n_fut_as_target += seen_tgt
    out[name] = {'val_checked': n, 'with_overlapping_train_clip': n_overlap, 'same_drive': n_same_av,
                 'target_future_fully_in_train': n_fut, 'as_train_target': n_fut_as_target, 'examples': examples}
    print(name, out[name], flush=True)
json.dump(out, open('/w/leak_stats_%s.json' % '_'.join(sys.argv[1:] or ['all']), 'w'), indent=1)
