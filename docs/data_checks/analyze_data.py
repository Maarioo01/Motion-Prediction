"""Column statistics for every V2X-Seq-TFD / V2X-Traj file type, from a seeded sample.

Run inside motion-prediction/v2x-graph (pandas, numpy). Mounts:
  /data/tfd  -> V2X-Seq-TFD root (read-only)
  /data/traj -> V2X-Traj root (read-only)
  /s         -> /raid/scratch/v2xgraph_data (read-only)
Writes JSON to /w/data_stats.json.
"""
import glob, json, os, random, sys
import numpy as np
import pandas as pd

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
random.seed(0)

C = '/data/tfd/cooperative-vehicle-infrastructure'
VIEWS = {
    'tfd/vehicle': (C + '/vehicle-trajectories/{s}', '*.csv'),
    'tfd/infrastructure': (C + '/infrastructure-trajectories/{s}', '*.csv'),
    'tfd/cooperative': (C + '/cooperative-trajectories/{s}', '*.csv'),
    'tfd/traffic-light': (C + '/traffic-light/{s}', '*.csv'),
    'tfd/single-vehicle': ('/data/tfd/single-vehicle/trajectories/{s}', '*.csv'),
    'tfd/single-infrastructure': ('/data/tfd/single-infrastructure/trajectories/{s}', '*.csv'),
    'tfd/labels': ('/s/tfd/cooperative-vehicle-infrastructure/traj_match_labels/{s}/data', '*.csv'),
    'traj/ego': ('/data/traj/ego-trajectories/{s}/data', '*.csv'),
    'traj/infrastructure': ('/data/traj/infrastructure-trajectories/{s}/data', '*.csv'),
    'traj/vehicle': ('/data/traj/vehicle-trajectories/{s}/data', '*.csv'),
    'traj/traffic-light': ('/data/traj/traffic-light/{s}/data', '*.csv'),
    'traj/labels': ('/s/v2x-traj/traj_match_labels/{s}/data', '*.csv'),
}


def col_stats(s):
    out = {'dtype': str(s.dtype), 'missing': int(s.isna().sum())}
    if s.dtype == object or s.nunique() <= 12:
        vc = s.astype(str).value_counts()
        out['n_unique'] = int(len(vc))
        out['values'] = {k: int(v) for k, v in vc.head(16).items()}
    else:
        v = s.dropna().astype(float)
        out['n_unique'] = int(s.nunique())
        q = np.percentile(v, [0, 1, 50, 99, 100]) if len(v) else [None] * 5
        out.update({'min': q[0], 'p1': q[1], 'median': q[2], 'p99': q[3], 'max': q[4]})
    return out


res = {}
for name, (pat, glb) in VIEWS.items():
    entry = {'files': {}, 'per_file': {}}
    frames = []
    for split in ['train', 'val']:
        d = pat.format(s=split)
        files = sorted(glob.glob(os.path.join(d, glb)))
        entry['files'][split] = len(files)
        for f in random.sample(files, min(N, len(files))):
            df = pd.read_csv(f)
            df['_file'] = os.path.basename(f)
            df['_split'] = split
            frames.append(df)
    if not frames:
        res[name] = entry
        continue
    df = pd.concat(frames, ignore_index=True)
    cols = [c for c in df.columns if not c.startswith('_')]
    entry['columns'] = {c: col_stats(df[c]) for c in cols}
    g = df.groupby('_file')
    entry['per_file']['rows'] = np.percentile(g.size(), [0, 50, 100]).tolist()
    if 'timestamp' in df:
        ts = g['timestamp'].agg(lambda x: x.max() - x.min())
        entry['per_file']['duration_s'] = np.percentile(ts, [0, 50, 100]).round(2).tolist()
        entry['per_file']['n_timestamps'] = np.percentile(g['timestamp'].nunique(), [0, 50, 100]).tolist()
    if 'id' in df:
        entry['per_file']['n_ids'] = np.percentile(g['id'].nunique(), [0, 50, 100]).tolist()
    if 'tag' in df:
        tgt = df[df.tag == 'TARGET_AGENT'].groupby('_file')['id'].nunique()
        entry['per_file']['target_ids_per_file'] = tgt.value_counts().to_dict() if len(tgt) else {}
        av = df[df.tag == 'AV'].groupby('_file').size()
        entry['per_file']['av_rows_per_file'] = np.percentile(av, [0, 50, 100]).tolist() if len(av) else None
    res[name] = entry
    print(name, entry['files'], len(df), 'rows sampled', flush=True)

json.dump(res, open('/w/data_stats.json', 'w'), indent=1, default=float)
print('done')
