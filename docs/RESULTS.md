# Results ledger

Every number that may go into the benchmark (checklist C3). A row needs: upstream commit,
local patches, checkpoint (sha256 prefix), config, seed, split, and the log path. Logs
are under `/raid/scratch/v2xgraph_data/logs/eval/` (not in git).

Metrics: minADE / minFDE / MR at K = 6, in metres, as computed by each repo's own
`eval.py`. Horizon: V2X-Seq-TFD 5 s (50 steps at 10 Hz) after 5 s of history; V2X-Traj
4 s (40 steps) after 4 s.

## Protocol for benchmark runs (decided 2026-11-24)

Applies to every number in the paper-1 tables. Rows produced with official checkpoints
(below) are sanity checks of our setup, not benchmark rows.

1. **No test set is released, so the official val split is our test set.** Nothing is
   chosen on it: no checkpoint selection, no early stopping, no hyperparameter search.
2. **Checkpoint = the last one** of a fixed schedule: each method's published number of
   epochs and learning-rate schedule. Upstream "best val" checkpoints are ignored. If a
   method turns out unstable at the end of training, hold out part of train for selection
   instead (decide per method, record it).
3. **Retrain every method, 3 seeds** (report mean and spread). V2X-Graph: `--seed` from
   patch 0003.
4. **One image per row, the `*-cu128` one**, so any run can go on either card. The same
   seed gives different weights in the two images, so seeds of one row never mix images.
5. **Same effective batch as published.** On one card, gradient accumulation makes up
   for the paper's GPU count (V2X-Graph: 4 GPUs × 1 × 16 → 1 GPU × 4 × 16 = 64 scenarios
   per update). Note: V2X-Graph averages its loss over all agents in a batch, so 4
   scenarios on one card weight crowded scenes slightly differently than 4 cards with 1
   each.
6. **Record** with every number: upstream commit, patches, config and flags, seed,
   split, image, card, log path.

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

## cu128 port validation (2026-11-16, RTX 5090)

Not benchmark numbers: these check that the `*-cu128` images (torch 2.7.1 + CUDA 12.8,
the only ones that run on the 5090) compute the same thing as the original images. Same
checkpoint, same preprocessed data, same seed; only image and card differ.

| Method / checkpoint | Split | Original image, RTX 3090 | cu128 image, RTX 5090 | Max difference |
| --- | --- | --- | --- | --- |
| V2X-Graph `v2x-seq-tfd/v2i.ckpt` (commit `b6cf34b`, patches 0001 + 0002) | TFD val | torch 1.12.1+cu116, PL 1.5.2: 1.0464418 / 1.7870295 / 0.2544726 | torch 2.7.1+cu128, PL 1.9.5: 1.0464418 / 1.7870294 / 0.2544726 | 1e-7 (minFDE) |
| QCNet `QCNet_AV2.ckpt` (official) | AV2 val, 24,988 scenarios | torch 2.0.1+cu118, PyG 2.3.0: minADE₆ 0.720117, minFDE₆ 1.252745, MR₆ 0.157396, brier-minFDE₆ 1.874043, minFDE₁ 4.316225 | torch 2.7.1+cu128, PyG 2.6.1, Python 3.10: identical to 6 decimals | 6e-8 |

Logs: `/raid/scratch/v2xgraph_data/logs/eval/tfd_val_v2i_cu128_gpu1.log`,
`outputs/qcnet_inference_cu128_gpu1/` (QCNet; the 3090 reference is `outputs/qcnet_inference/`).

Training smoke tests (40 steps + validation + checkpoint, both cards at the same time):
V2X-Graph TFD V2I, batch 4 — original image on the 3090 and cu128 on the 5090 both
complete, loss 8.8 → 6.0 on both; QCNet AV2 — cu128 image on the 3090 (batch 2) and on
the 5090 (batch 4, 9 GiB peak in these 40 steps) both complete. Same seed does **not**
give the same weights across the two torch versions, so a benchmark row must use one
image for all its seeds.

## Training speed (2026-11-24)

Not benchmark numbers. One full epoch of V2X-Graph, TFD train, V2I, `v2x-graph-cu128`,
batch 4 × accumulation 16, 12 workers, seed 2022, both cards at the same time, graph files
read from `/raid` (single 8 TB HDD):

| Card | Steps/s | Epoch (6,394 steps) | 64 epochs (estimate) |
| --- | --- | --- | --- |
| RTX 3090 | 1.21 | 88.3 min | ~94 h |
| RTX 5090 | 1.39 | 76.7 min | ~82 h |

Logs: `/raid/scratch/v2xgraph_data/logs/timing/`. No errors; peak allocated memory at
batch 4 is 8.9 GiB (nvidia-smi showed up to 23 / 30 GB, mostly the allocator's cache).

**Why the 5090 was barely faster.** Not the disk: with batches already in GPU memory the
5090 runs at the same 1.40 steps/s. The profiler puts 612 of 714 ms per step in one kernel,
the backward of `self.<lane attribute>_embed[index]` in `models/agent_lane_subgraph.py`:
690,000 indices into tables of 2–4 rows, which PyTorch's generic indexing backward handles
almost serially. Patch 0004 (V2X-Graph) and DAIR-V2X-Seq 0002 (HiVT, same code) use
`F.embedding` instead:

| Card | Original | With `F.embedding` | Speed-up |
| --- | --- | --- | --- |
| RTX 3090 | 1.24 steps/s | 5.91 steps/s | 4.8× |
| RTX 5090 | 1.39 steps/s | 11.17 steps/s | 8.0× |

Same computation: forward and loss identical (2.2361860 on the test batch). Gradients of
the three tables are closer to a float64 reference than the original's (max error
2.5e-8 – 3.0e-8 vs 6.2e-8 – 1.4e-7, gradient scale ~7e-3); all other parameters differ by
at most 5.5e-6, against 2.8e-6 between two runs of the unpatched code (atomic adds in PyG).

**After the fix the disk becomes the limit.** The DataLoader alone reads 7.4 batches/s
(29.6 scenarios/s) from `/raid` with 12 workers, below the 5090's 11.2, and two runs on the
same disk would share it. TFD train graph files: 84 GB (val 34 GB; V2X-Traj 25 + 8.1 GB).
