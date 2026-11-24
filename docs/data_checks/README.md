# Data checks

Small scripts behind the dataset facts in `docs/DATASETS.md` (splits) and the data page.
Run them in a GPU-less container with the datasets mounted read-only, e.g.:

```bash
docker run --rm --entrypoint bash -u 1000:1000 \
  -v /raid/datasets/V2X-Seq-TFD/V2X-Seq-TFD:/data/tfd:ro -v /raid/datasets/V2X-Traj/v2x-traj:/data/traj:ro \
  -v /raid/scratch/v2xgraph_data:/s:ro -v "$PWD/docs/data_checks":/w motion-prediction/v2x-graph:latest \
  -c 'python -I /w/split_analysis.py'      # or leak_check.py [tfd|traj], analyze_data.py 30
```

| Script | Output (`/w/…json`) | What it answers |
| --- | --- | --- |
| `analyze_data.py N` | `data_stats.json` | columns, value sets and ranges of every file type, from N scenarios per split |
| `split_analysis.py` | `split_stats.json` | recording days, intersections, time gaps between val and train clips |
| `leak_check.py [tfd\|traj]` | `leak_stats_<set>.json` | for 400 random val scenarios: same drive in train? whole target future present in a training file? |
| `clean_subset.py [GAP]` | `tfd_val_clean<GAP>s.txt`, `…_strict.txt` | leakage-free TFD val subset (protocol point 7): no train clip at the same intersection (strict: anywhere) within GAP s. The 60 s lists are committed here |

They read every scenario's first row (and, for `leak_check.py`, whole files) from the HDD:
expect 10–40 min each, longer while training reads from the same disk.
