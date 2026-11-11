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
and GPU0 on this machine (see [GPU allocation](#gpu-allocation) — the second card has
its own problems).

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

Planned V2X baselines (Phase 0 checklist B2-B5):

| Repo | Status | Dataset | Checkpoints | License |
|---|---|---|---|---|
| [V2X-Graph](https://github.com/AIR-THU/V2X-Graph) | ⏳ to add (B2) | V2X-Seq-TFD, V2X-Traj | ✅ in repo via Git LFS (needs `git lfs pull`) | Apache-2.0 |
| [V2I_trajectory_prediction](https://github.com/xichennn/V2I_trajectory_prediction) (V2INet) | ⏳ to add (B3); cloned by `setup.sh --all` | V2X-Seq-TFD | ❌ | none (all rights reserved by default) |
| [Co-MTP](https://github.com/xiaomiaozhang/Co-MTP) | ⏳ to add (B4) | V2X-Seq-TFD | ❌ | none stated |
| HiVT baseline ([DAIR-V2X-Seq](https://github.com/AIR-THU/DAIR-V2X-Seq) `projects/HiVT_plugin`) | ⏳ to add (B5); likely no separate service needed | V2X-Seq-TFD | ❌ not in repo (README expects `checkpoints/online.ckpt`) | Apache-2.0 (HiVT) |

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
   reservations.devices` block pinning `device_ids: ["0"]` (see "GPU allocation" below —
   never `gpus: all`), the right dataset volume mount(s) from `/raid` (read-only), and
   `./repos/<Name>:/workspace`. If the repo has its own preprocessing step that writes
   output under the repo (e.g. a `data_staging/` convention used by SceneInformer/
   GameFormer/TrajFlow), also mount scratch space from `/raid` over that specific
   subpath (`/raid/scratch/<name>_data_staging:/workspace/data_staging`) rather than
   letting it land on the OS disk — see the "repos/ lives on the OS disk" gotcha in
   `BUILD_GOTCHAS.md` for why this matters.
6. `./setup.sh && docker compose build <name>`, then iterate on failures.
7. Add an entry to the `CHECKS` array in `verify.sh` — a quick `python -c "import ...;
   assert torch.cuda.is_available()"` covering the key libraries and, if applicable, the
   compiled extension.
8. Update the Status table above and tick the item in `docs/v2x_plan/PHASE0_CHECKLIST.md`.

**Reproducibility note**: `setup.sh` clones the default branch's current HEAD, not a
pinned commit — fine for active development, but if you need a result to be exactly
reproducible later, record the commit hash `git -C repos/<Name> rev-parse HEAD` gives you
alongside that result.

## GPU allocation

**GPU0 (RTX 3090) only, by design.** This machine has a second card (a 3090 Ti,
GPU index 1) that has repeatedly wedged under load — `nvidia-smi` reports `Unable to
determine the device handle: Unknown Error` with no process attached, and doesn't
self-recover reliably. Worse, once it's in that state, `nvidia-container-cli` fails to
launch *any* GPU container at all (it enumerates every GPU on the system regardless of
which one you actually request), so a bad GPU1 blocks GPU0 too. Every service in
`docker-compose.yml` is pinned to `device_ids: ["0"]` explicitly (not `gpus: all`) for
exactly this reason — don't change this back without a real fix for GPU1's stability
first, and don't add a service or ad-hoc `docker run` that requests GPU1 or `all`.

If a container fails to start with `nvidia-container-cli: detection error: nvml error`,
that's this issue recurring, not a config problem — check `nvidia-smi` for GPU1's
status before assuming anything else is broken. Recovery is `sudo nvidia-smi -r -i 1`
(resets only GPU1, not the whole machine, no reboot); if that doesn't clear it, don't
escalate to a reboot unilaterally if no one has physical access to the machine.

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
