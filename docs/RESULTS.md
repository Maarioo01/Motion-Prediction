# Results ledger

Every number that may go into the benchmark (checklist C3). A row needs: upstream commit,
local patches, checkpoint (sha256 prefix), config, seed, split, and the log path. Logs
are under `/raid/scratch/v2xgraph_data/logs/eval/` (not in git).

Metrics: minADE / minFDE / MR at K = 6, in metres, over the 5 s horizon (50 steps at 10 Hz),
as computed by each repo's own `eval.py`.

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
