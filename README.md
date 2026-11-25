# Motion Prediction

A local benchmark bench for V2X motion forecasting research: one Docker environment per
upstream model repo, each runnable in isolation against shared, locally-mounted datasets.
The bench originally held 11 built repos; since Nov 2026 only the V2X-relevant ones are
active and the rest are archived in [`docker/_archive/`](docker/_archive/README.md). Built to let a single researcher quickly try a new
idea against several published baselines without fighting Python/CUDA version hell for
each one individually.

> **Current plan (Nov 2026): V2X only, real datasets only.** Start with
> [`docs/v2x_plan/PHASE0_CHECKLIST.md`](docs/v2x_plan/PHASE0_CHECKLIST.md), the report
> [`docs/v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md`](docs/v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md)
> ([PDF with colour marks](docs/v2x_plan/INFORME_PLAN_DE_RUTA_V2X.pdf)) and the first-paper
> summary [`docs/v2x_plan/PAPER1_V2X_BENCHMARK.md`](docs/v2x_plan/PAPER1_V2X_BENCHMARK.md).
> Claude Code sessions: see [`CLAUDE.md`](CLAUDE.md). The bench's model list below has been
> trimmed to the V2X baselines (checklist B1; see CLAUDE.md, "Methods").

See [`docs/PHD_ROADMAP.md`](docs/PHD_ROADMAP.md) (superseded) for the earlier PhD
plan, and [`docs/REPO_ASSESSMENT.md`](docs/REPO_ASSESSMENT.md) for a critical read on
which of these repos are actually worth building on versus just useful as reference
baselines.

*History:* 12 of the 13 originally investigated repos came from the original survey's ranked shortlist (10 built, 2 investigated
but skipped — see [`docs/DATASETS.md`](docs/DATASETS.md)). The 13th, **MTR**, was added
later on purpose: it's the baseline nearly every other repo here reports numbers
against, and CMP's own prediction stage is literally an MTR-based module — see
[`docs/MODELS_OVERVIEW.md`](docs/MODELS_OVERVIEW.md) for why it earned a spot despite
not being in the survey's own corpus, and why its newer MTR++ successor was
deliberately *not* added instead (its code was never publicly released).

## Why one Docker image per repo

Every repo here pins its own, usually incompatible, Python/PyTorch/CUDA combination —
they range from Python 3.7 to 3.10, CUDA 11.1 to 12.1, and several pull in TensorFlow
alongside PyTorch. A single shared environment isn't feasible; isolation is the point.
What's shared instead: this one `docker-compose.yml`, the dataset mounts from `/raid`,
and the two GPUs on this machine, one experiment per card (see
[GPU allocation](#gpu-allocation)).

## Quick start

```bash
git clone https://github.com/Maarioo01/Motion-Prediction.git && cd Motion-Prediction

# 1. Fetch the upstream model repos (not tracked in this repo - see "Repository
#    structure" below for why) and overlay this project's Dockerfiles onto them.
./setup.sh

# 2. Build everything (or just one: docker compose build qcnet)
docker compose build

# 3. Confirm every environment actually works (imports, compiled CUDA ops, GPU visible)
./verify.sh

# 4. Get a shell in any one of them
docker compose run --rm qcnet bash
```

## Repository structure

```
MOTION_PREDICTION/
  docker-compose.yml     # one service per active repo; GPUs + dataset mounts + build config
  setup.sh               # clones repos/<Name> from upstream, overlays docker/<Name>/*
  verify.sh              # runs a quick import+CUDA sanity check against every service
  docker/_archive/        # TRACKED: configs of repos removed from the active bench
  docker/<Name>/          # TRACKED: this project's own files for each repo
    Dockerfile
    entrypoint.sh          # only present where something needs building at container
                            # start (see "Adding a new repo" below)
    requirements-docker.txt # only present where the upstream requirements.txt needed
                            # patching or didn't exist - overlaid onto repos/<Name>/
                            # as requirements.txt by setup.sh
  repos/<Name>/            # GITIGNORED: fresh clone of the upstream repo + the
                            # overlaid docker/<Name>/* files on top. Recreated by
                            # setup.sh, safe to delete and regenerate at any time.
  docs/
    BUILD_GOTCHAS.md      # real build issues hit and how they were fixed - read this
                            # before adding a new repo, the same problems recur
    DATASETS.md            # exact access steps for the two remaining dataset gaps
    PHD_ROADMAP.md
    REPO_ASSESSMENT.md
    SURVEY_itss.pdf         # the survey this whole shortlist was drawn from
    repository-shortlist-notes.pdf/.docx  # original scratch notes the shortlist came from
```

**Why upstream repos aren't committed here**: several bundle datasets or large assets
in-repo (pretraining-synthetic ships a 2.3GB synthetic dataset; a couple others carry
100MB+ of images/checkpoints), collectively multiple GB — well past what's sane to
duplicate into a git repo, and it would blur licensing between "this project's own
work" and "code copied from ten different upstream authors." `setup.sh` fetches them
fresh instead, at whatever commit is current upstream (not pinned - see the note in
"Adding a repo" below if you want reproducibility pinning later).

## Status

Active services (in `setup.sh` and `docker-compose.yml`):

| Repo | Status | Dataset | Checkpoints | License |
|---|---|---|---|---|
| [QCNet](https://github.com/ZikangZhou/QCNet) | ✅ working, **trained from scratch (64 epochs) + official checkpoint reproduces the paper exactly** - see [`TRAINING_PLAN.md`](docs/TRAINING_PLAN.md). Base for our own model; to be adapted to V2X-Seq | `/raid/argoverse2` (present); preprocessed caches in `/raid/scratch/qcnet_data_staging` | ✅ [AV2 marginal](https://drive.google.com/file/d/1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv/view) | Apache-2.0 |
| [CMP](https://github.com/tasl-lab/CMP) | ✅ working (env); V2V4Real only (checklist D1) | `/raid/datasets/V2V4Real` (present) | see repo's `docs/prepare_dataset_checkpoints.md` | none stated |
| [V2X-Graph](https://github.com/AIR-THU/V2X-Graph) | ✅ **official TFD checkpoints reproduce the paper** (TFD V2I 1.05 / 1.79 / 0.25 on val; V2X-Traj V2I/V2V/V2X too, ego ckpt does not, see [`RESULTS.md`](docs/RESULTS.md)) | `/raid/datasets/V2X-Seq-TFD`, `/raid/datasets/V2X-Traj` (present); layout + caches in `/raid/scratch/v2xgraph_data` | ✅ in repo via Git LFS (entrypoint fetches them) | Apache-2.0 |
| HiVT baseline ([DAIR-V2X-Seq](https://github.com/AIR-THU/DAIR-V2X-Seq) `projects/HiVT_plugin`) | ✅ **all three official checkpoints reproduce** (online 1.26 / 2.34 / 0.35, none, offline; `hivt-cu128`, no own image); protocol retraining running | `/raid/datasets/V2X-Seq-TFD`; layout + caches in `/raid/scratch/hivt_data` (fused train set on the NVMe) | ✅ Google Drive, linked from its `docs/benchmarks/vic-traj-forecasting/README.md` | Apache-2.0 (HiVT) |
| [V2I_trajectory_prediction](https://github.com/xichennn/V2I_trajectory_prediction) (V2INet) | ✅ runs (`v2inet-cu128`, 4 patches); no checkpoint, so a retrain is the reproduction (paper: 1.19 / 1.98 / 0.27) | `/raid/datasets/V2X-Seq-TFD`; layout + caches in `/raid/scratch/v2inet_data` | ❌ none released | none (all rights reserved by default) |

Planned V2X baseline (Phase 0 checklist B4):

| Repo | Status | Dataset | Checkpoints | License |
|---|---|---|---|---|
| [Co-MTP](https://github.com/xiaomiaozhang/Co-MTP) | ⏳ to add (B4) | V2X-Seq-TFD | ❌ | none stated |

Archived (configs in [`docker/_archive/`](docker/_archive/README.md), not built or run):
UniTraj, GameFormer, TrajFlow, MTR, SceneInformer, RealMotion, emp,
Pretraining-on-Synthetic, UniAD. StreamingForecasting was dropped from `setup.sh --all`
(never built). See the archive README for upstream URLs and how to restore one.

## Datasets

Real datasets only (see CLAUDE.md). V2X-Seq-TFD (train + val) and V2X-Traj come from the
official public Google Drive links in the `AIR-THU/DAIR-V2X` and `AIR-THU/V2X-Graph`
READMEs and go to `/raid/datasets/V2X-Seq-TFD` and `/raid/datasets/V2X-Traj`
(checklist A1/A2). V2V4Real is at `/raid/datasets/V2V4Real` (CMP). Argoverse 2 stays for
QCNet. The keep/delete list for the rest of `/raid` is in CLAUDE.md, "Datasets"; see
[`docs/DATASETS.md`](docs/DATASETS.md) for what is on disk.

## Training from scratch / running inference

General pattern: `docker compose run --rm <service> bash`, then follow that repo's own
README (present at `repos/<Name>/README.md` after `setup.sh`) — commands below are
copied from what's actually documented upstream, verified during this project's
build/test process:

```bash
# QCNet - the upstream README's commands do NOT work as-is here (read-only data mount, our
# dataset layout, and batch 4 runs out of memory on one 24GB card). Verified train + inference
# commands are in docs/TRAINING_PLAN.md ("QCNet: trained from scratch + validated").
# Inference/eval + plots: qcnet_inference.py (from docker/QCNet/extras/), results in outputs/qcnet_inference/

# Every command below also works with the 5090-capable images: replace `qcnet` / `v2x-graph` by
# `qcnet-cu128` / `v2x-graph-cu128` (GPU 1 by default, `GPU=0` for the 3090); see "GPU allocation".

# V2X-Graph on V2X-Seq-TFD (data layout: see docs/BUILD_GOTCHAS.md, "V2X-Graph")
docker compose run --rm v2x-graph bash prepare_tfd_layout.sh
docker compose run --rm v2x-graph python /deps/DAIR-V2X-Seq/tools/data_converter/maps_merge.py --data_root /workspace/data_staging/tfd
docker compose run --rm v2x-graph bash -c "cd traj_match_labels && python generate_label.py --data_root /workspace/data_staging/tfd --dataset V2X-Seq-TFD"
# Not upstream preprocess.py (serial, ~35 h, OOM-killed at 62 GB): same per-scenario code, 6 workers, ~1 scen/s
for s in val train; do docker compose run --rm -e PYTHONHASHSEED=0 v2x-graph python preprocess_parallel.py \
  --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure --split $s --workers 6; done
# Train one benchmark row on one card (protocol in docs/RESULTS.md): 64 scenarios per update, last.ckpt is reported
GPU=1 docker compose run --rm v2x-graph-cu128 python train.py --dataset V2X-Seq-TFD --cooperation v2i \
  --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure --gpus 1 --train_batch_size 4 \
  --accumulate_grad_batches 16 --num_workers 12 --seed 2022 --default_root_dir /workspace/data_staging/runs/tfd_v2i_s2022

# HiVT, official V2X-Seq baseline (DAIR-V2X-Seq projects/HiVT_plugin; reuses the v2x-graph cu128 image).
# Its cooperative ("online", PP-VIC) input is a rule-based fusion of both views into one track per object.
docker compose run --rm hivt-cu128 bash /bench-extras/prepare_tfd_layout.sh /data/v2x-seq-tfd /workspace/data_staging/tfd
cp /raid/scratch/v2xgraph_data/tfd/map_files/* /raid/scratch/hivt_data/tfd/map_files/   # same maps_merge.py output
for s in val train; do docker compose run --rm hivt-cu128 bash -c "\
  python /workspace/tools/trajectory_fusion/fusion_for_prediction.py --data_root /workspace/data_staging/tfd --split $s && \
  python /workspace/tools/data_converter/tfd_converter.py --data_root /workspace/data_staging/tfd --split $s"; done
docker compose run --rm hivt-cu128 python eval.py --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure/fusion_for_prediction --ckpt_path <ckpt>
# Train one HiVT online seed under the protocol: the published config of the official "online" checkpoint
# (lr 3e-4, 2 GPUs x 16 -> here 16 x accumulation 2, 64 epochs); last.ckpt is reported (DAIR patch 0004)
GPU=1 docker compose run --rm -u 1000:1000 -e MPLCONFIGDIR=/tmp hivt-cu128 python train.py \
  --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure/fusion_for_prediction --train_batch_size 16 \
  --accumulate_grad_batches 2 --lr 3e-4 --max_epochs 64 --num_workers 8 --seed 2022 \
  --default_root_dir /workspace/data_staging/runs/tfd_online/seed2022

# V2INet (B3; reuses the v2x-graph cu128 image). Car and roadside tracks become separate graph nodes (no association).
docker compose run --rm v2inet-cu128 bash prepare_tfd_layout.sh          # writable symlink tree in /raid/scratch/v2inet_data
cp -r /raid/scratch/v2xgraph_data/tfd/map_files /raid/scratch/v2inet_data/tfd/   # same maps_merge.py output
# Not upstream's serial loop: same per-scenario code (process_argoverse), 10 workers, resumable
for s in val train; do docker compose run --rm -e PYTHONHASHSEED=0 v2inet-cu128 python preprocess_parallel.py \
  --root /workspace/data_staging/tfd/cooperative-vehicle-infrastructure/vehicle-trajectories --split $s --workers 10; done

# V2X-Graph on V2X-Traj (ships in the expected layout with prebuilt map_files; no map merge)
docker compose run --rm v2x-graph bash prepare_v2xtraj_layout.sh
docker compose run --rm -e DATA_ROOT=/workspace/data_staging/v2x-traj v2x-graph bash -c "cd traj_match_labels && python generate_label.py --data_root /workspace/data_staging/v2x-traj --dataset V2X-Traj"
for s in val train; do docker compose run --rm -e DATA_ROOT=/workspace/data_staging/v2x-traj -e PYTHONHASHSEED=0 v2x-graph python preprocess_parallel.py \
  --dataset V2X-Traj --root /workspace/data_staging/v2x-traj --split $s --workers 6; done
```

For **CMP**, the exact flags weren't double-checked yet — get a shell and read the repo's
own README/`docs/` first (`docker compose run --rm cmp bash`, then `cat README.md`); the
environment is confirmed working, only the exact CLI invocation is left to the repo's
own documentation. Commands for the archived repos are in git history.

Checkpoints (where available, see the Status table) go through Google Drive links
in each repo's own README — download them yourself and mount or `docker cp` them into
the container, then pass the path via that repo's `--ckpt_path`/`checkpoint=`/similar
flag as shown above.

## Verifying everything works

```bash
./verify.sh                 # all active services
./verify.sh qcnet           # just this one
```

This isn't a model-correctness test — it's the same import+CUDA sanity check used
while originally building each image (torch/CUDA visible, key libraries importable,
compiled extensions loadable). A model actually training correctly is a separate,
much larger claim this script doesn't make.

## Adding a new repo

This is the exact recipe followed for every repo built here — expect real iteration
(rebuild, read the error, fix, repeat), not a one-shot process. Read
[`docs/BUILD_GOTCHAS.md`](docs/BUILD_GOTCHAS.md) first; the same handful of root causes
account for nearly every build failure hit so far.

1. `git clone --depth 1 <upstream-url> /tmp/scratch-clone` and read its README /
   `environment.yml` / `requirements.txt` to find the exact Python/PyTorch/CUDA pin it
   expects, and whether it compiles any custom CUDA extensions (`setup.py` importing
   `torch.utils.cpp_extension.CUDAExtension` is the tell).
2. `mkdir docker/<Name>` and write `docker/<Name>/Dockerfile`. Pick the closest existing
   template:
   - Pure pip, no custom CUDA ops → `docker/QCNet` or `docker/_archive/GameFormer`.
   - Compiles custom CUDA ops (knn/attention/etc.) → `docker/_archive/TrajFlow` or
     `docker/_archive/UniTraj`: needs a `cuda-toolkit` + matching `gcc`/`gxx` conda install (see
     gotchas), and an `entrypoint.sh` that builds the extension against the *mounted*
     source at container start rather than baking it into the image, so the repo stays
     live-editable. Copy `docker/_archive/TrajFlow/entrypoint.sh` as a starting point.
   - Repo ships its own official `docker/Dockerfile` → adapt it (see `docker/_archive/UniAD` and
     the corresponding gotcha) rather than writing one from scratch.
3. If the upstream `requirements.txt` needs patching (unpinned `torch`, a version with
   no wheel for that Python, etc.) or doesn't exist, write
   `docker/<Name>/requirements-docker.txt` — `setup.sh` overlays it onto
   `repos/<Name>/requirements.txt` at fetch time.
4. Add the repo + its clone URL to the `REPOS` array in `setup.sh`.
5. Add a service block to `docker-compose.yml`, copying an existing one: `build:
   ./repos/<Name>`, `image: motion-prediction/<name>:latest`, the `deploy.resources.
   reservations.devices` block (`deploy: *gpu-3090-only` for an old-CUDA image,
   `deploy: *gpu-any` for a CUDA ≥ 12.8 one; see "GPU allocation" below — never `gpus: all`), the right dataset volume mount(s) from `/raid` (read-only), and
   `./repos/<Name>:/workspace`. If the repo has its own preprocessing step that writes
   output under the repo (e.g. a `data_staging/` convention used by SceneInformer/
   GameFormer/TrajFlow), also mount scratch space from `/raid` over that specific
   subpath (`/raid/scratch/<name>_data_staging:/workspace/data_staging`) rather than
   letting it land on the OS disk — see the "repos/ lives on the OS disk" gotcha in
   `BUILD_GOTCHAS.md` for why this matters.
6. `./setup.sh && docker compose build <name>`, then iterate on failures.
   If the upstream pins cannot run on the 5090, also add `docker/<Name>/Dockerfile.cu128`
   and a `<name>-cu128` service (copy `v2x-graph-cu128`), and validate it against the
   original image before using it for results.
7. Add an entry to the `CHECKS` array in `verify.sh` — a quick `python -c "import ...;
   assert torch.cuda.is_available()"` covering the key libraries and, if applicable, the
   compiled extension.
8. Update the Status table above and tick the item in `docs/v2x_plan/PHASE0_CHECKLIST.md`.

**Reproducibility note**: `setup.sh` clones the default branch's current HEAD, not a
pinned commit — fine for active development, but if you need a result to be exactly
reproducible later, record the commit hash `git -C repos/<Name> rev-parse HEAD` gives you
alongside that result.

## GPU allocation

Two cards since 2026-11-16 (the unstable 3090 Ti was replaced by an RTX 5090):

| `nvidia-smi` index | Card | Memory | Images that run on it |
| --- | --- | --- | --- |
| 0 | RTX 3090 | 24 GB | all (`qcnet`, `cmp`, `v2x-graph` and the `*-cu128` ones) |
| 1 | RTX 5090 | 32 GB | only `*-cu128` (`qcnet-cu128`, `v2x-graph-cu128`, `hivt-cu128`, `v2inet-cu128`) |

**Why two images per repo.** The 5090 needs PyTorch built for CUDA ≥ 12.8 (torch ≥ 2.7);
the upstream pins (torch 1.12 / 1.13 / 2.0 on CUDA 11.x) cannot run on it. Each ported
repo therefore has a second image, `docker/<Name>/Dockerfile.cu128` → service
`<name>-cu128`, with the same code, mounts and data. The original image stays as the
reference that reproduces the published numbers; the cu128 image is validated against it
(see [`docs/RESULTS.md`](docs/RESULTS.md), "cu128 port validation"). CMP is not ported
yet (Python 3.7 + spconv + compiled CUDA ops) and is 3090-only.

**How to pick a card.** One card per container, chosen with the `GPU` variable; never
`gpus: all` and no multi-GPU training across the two (different speed and memory —
run one experiment or seed per card instead).

```bash
docker compose run --rm v2x-graph-cu128          # default for *-cu128: GPU 1 (5090)
GPU=0 docker compose run --rm v2x-graph-cu128    # same image on the 3090
docker compose run --rm v2x-graph                # original image: always GPU 0
./verify.sh                                      # checks every image on every card it supports
```

Check `nvidia-smi` before launching: a card that already runs a training job should not
get a second one. For the benchmark, keep one image per experiment family (do not mix
original and cu128 runs among the seeds of one table row), and record image + card with
every number.

**Known hardware notes (2026-11-16 load test).** Both cards at 100 % together draw
~930 W (5090 ≈ 600 W, 3090 ≈ 340 W) and ran stable. The 3090 reaches its thermal limit
(84–87 °C, fan 100 %) and throttles itself, also when running alone; the 5090 peaks at
~76 °C. Both slots run at PCIe ×8.

**If `nvidia-smi` fails after a reboot** ("couldn't communicate with the NVIDIA
driver"): an automatic kernel update arrived without the matching NVIDIA modules. Fix:
`sudo apt install linux-modules-nvidia-580-open-generic-hwe-24.04 nvidia-driver-580-open`
and reboot (this happened on 2026-11-16 with kernel 7.0.0-43).

## Docs

- [`docs/BUILD_GOTCHAS.md`](docs/BUILD_GOTCHAS.md) — real build issues and fixes, worth
  reading before adding a repo.
- [`docs/DATASETS.md`](docs/DATASETS.md) — dataset status and exact steps for the
  remaining Waymo `scenario` gap.
- [`docs/TRAINING_PLAN.md`](docs/TRAINING_PLAN.md) — which repos need training from
  scratch to get any result at all (no checkpoint exists), a sane order to attempt
  them in, and realistic expectations for 2 GPUs vs. the 4-8 most papers used.
- [`docs/REPO_ASSESSMENT.md`](docs/REPO_ASSESSMENT.md) — which of these 11 are actually
  worth building on as a research baseline versus just useful for comparison, and what's
  missing from the shortlist entirely.
- [`docs/MODELS_OVERVIEW.md`](docs/MODELS_OVERVIEW.md) — a literature-review-style
  reference covering all 12 repos (the 10 built + the 2 skipped): architecture,
  datasets, metrics, reported results (pulled from each paper, not just the README),
  license, and limitations, plus comparison figures (dataset-usage matrix, a
  shared-benchmark similarity matrix, and a direct Argoverse 2 head-to-head where one
  is actually meaningful).
- **[Bearing & Bench](https://claude.ai/code/artifact/822a6791-32af-4d7e-8f69-ee138f1f16a6)**
  — a single-page read combining `REPO_ASSESSMENT.md` and `PHD_ROADMAP.md`, if that's
  easier to read in one sitting than two markdown files.
- [`docs/PHD_ROADMAP.md`](docs/PHD_ROADMAP.md) — how this benchmark fits into a 2-3 year
  PhD plan aimed at V2X motion forecasting.
