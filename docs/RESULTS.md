# Results ledger

Every number that may go into the benchmark (checklist C3). A row needs: upstream commit,
local patches, checkpoint (sha256 prefix), config, seed, split, and the log path. Logs
are under `/raid/scratch/v2xgraph_data/logs/eval/` (not in git).

Metrics: minADE / minFDE / MR at K = 6, in metres, as computed by each repo's own
`eval.py`. Horizon: V2X-Seq-TFD 5 s (50 steps at 10 Hz) after 5 s of history; V2X-Traj
4 s (40 steps) after 4 s.

## V2X-Seq-TFD, val split (test not released)

| Date | Method | Cooperation | minADE | minFDE | MR | Published | Upstream commit | Patches | Checkpoint (sha256) | Config | Seed | Log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-12 | V2X-Graph (official ckpt) | V2I | **1.046** | **1.787** | **0.254** | 1.05 / 1.79 / 0.25 | `b6cf34b` | 0001 (PyG `__inc__`) | `v2x-seq-tfd/v2i.ckpt` (`af78366b60243ada`) | ckpt hparams; `eval.py --batch_size 8` | 2022 (fixed in `eval.py`) | `tfd_val_v2i.log` |
| 2026-11-12 | V2X-Graph (official ckpt) | ego only | **1.160** | **2.021** | **0.303** | 1.16 / 2.02 / 0.30 | `b6cf34b` | 0001 | `v2x-seq-tfd/ego.ckpt` (`76b406977e3e1395`) | same | 2022 | `tfd_val_ego.log` |

Both reproduce the paper to the reported precision (C2). Preprocessing: `prepare_tfd_layout.sh`
→ `maps_merge.py` (DAIR-V2X-Seq `8a5b4f8`) → `generate_label.py` → `preprocess_parallel.py`
(`PYTHONHASHSEED=0`; output-identical to upstream `preprocess.py`, see BUILD_GOTCHAS.md).
Val caches: 10,229 scenarios in `/raid/scratch/v2xgraph_data/tfd/cooperative-vehicle-infrastructure/v2x_fusion/val/processed`.
Side metrics printed by `eval.py` (V2X association): V2I Precision 0.872 / Recall 0.872;
ego 0.864 / 0.858.

## V2X-Traj, val split (test not released)

| Date | Method | Cooperation | minADE | minFDE | MR | Published | Upstream commit | Patches | Checkpoint (sha256) | Config | Seed | Log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-12 | V2X-Graph (official ckpt) | ego only | 0.960 | 1.699 | 0.200 | 0.90 / 1.56 / 0.17 | `b6cf34b` | 0001 | `v2x-traj/ego.ckpt` minus 1 unused key (`7dcb6006b72be49c`; original `ego.ckpt`) | ckpt hparams; `eval.py --batch_size 8` | 2022 | `v2xtraj_val_ego.log` |
| 2026-11-12 | V2X-Graph (official ckpt) | V2I | **0.797** | **1.293** | **0.136** | 0.80 / 1.32 / 0.13 | `b6cf34b` | 0001 | `v2x-traj/v2i.ckpt` (`597d8f780afdd8de`) | same | 2022 | `v2xtraj_val_v2i.log` |
| 2026-11-12 | V2X-Graph (official ckpt) | V2V | **0.773** | **1.256** | **0.115** | 0.77 / 1.26 / 0.12 | `b6cf34b` | 0001 | `v2x-traj/v2v.ckpt` (`8d93636ac700c184`) | same | 2022 | `v2xtraj_val_v2v.log` |
| 2026-11-12 | V2X-Graph (official ckpt) | V2X | **0.714** | **1.126** | **0.105** | 0.72 / 0.13 (sic) / 0.11 | `b6cf34b` | 0001 | `v2x-traj/v2x.ckpt` (`1095ca57d4fd3c04`) | same | 2022 | `v2xtraj_val_v2x.log` |

V2I, V2V and V2X reproduce the published numbers (minFDE 1.126 confirms the README's
"0.13" is a typo for 1.13). **Ego-only does not** (+7 % minADE, +9 % minFDE, +18 % MR).
The released `ego.ckpt` has a parameter (`interpretable_graph._motion_embed`, 1×128)
that the released code no longer defines, so it was trained with an earlier version of
the code; strict loading fails until that key is dropped (copy at
`/raid/scratch/v2xgraph_data/ckpt_clean/v2x-traj/ego.ckpt`, strict load of all other
keys OK). Most likely the forward pass changed too, so this row is **not a valid
reproduction**; for the benchmark the V2X-Traj ego baseline must be retrained from the
released code. Association metrics (Precision / Recall): ego 0.525 / 0.506, V2I 0.749 /
0.757, V2V 0.755 / 0.762, V2X 0.753 / 0.761. Val caches: 2,020 scenarios in
`/raid/scratch/v2xgraph_data/v2x-traj/v2x_test/val/processed`.
