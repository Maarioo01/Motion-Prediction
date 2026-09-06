# Motion Prediction

A local benchmark bench for motion forecasting research: Docker environments for 10
(of 12 investigated) motion-forecasting repos, each runnable in isolation against
shared, locally-mounted datasets. Built to let a single researcher quickly try a new
idea against several published baselines without fighting Python/CUDA version hell for
each one individually.

See [`docs/PHD_ROADMAP.md`](docs/PHD_ROADMAP.md) for how this fits into the broader PhD
plan, and [`docs/REPO_ASSESSMENT.md`](docs/REPO_ASSESSMENT.md) for a critical read on
which of these repos are actually worth building on versus just useful as reference
baselines.

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
  docker-compose.yml     # one service per repo; GPUs + dataset mounts + build config
  setup.sh               # clones repos/<Name> from upstream, overlays docker/<Name>/*
  verify.sh              # runs a quick import+CUDA sanity check against every service
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

| Repo | Rank in survey | Status | Dataset | Checkpoints | License |
|---|---|---|---|---|---|
| [QCNet](https://github.com/ZikangZhou/QCNet) | 1 | ✅ working | `/raid/argoverse2` (present) | ✅ [AV2 marginal](https://drive.google.com/file/d/1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv/view) | Apache-2.0 |
| [UniTraj](https://github.com/vita-epfl/UniTraj) | 2 | ✅ working | AV2/Waymo/nuScenes (present; ScenarioNet conversion not run) | ❌ train-from-scratch by design | AGPLv3 (copyleft) |
| [GameFormer](https://github.com/MCZhi/GameFormer) | 3 | ✅ working, preprocessing verified | `/raid/waymo/scenario` — needs the plain `training` split (not yet downloaded, only `training_20s`); preprocessing verified end-to-end against `validation` (7403 `.npz` from 3 shards) after fixing a real upstream bug, see [`TRAINING_PLAN.md`](docs/TRAINING_PLAN.md) | ❌ | none stated |
| [RealMotion](https://github.com/fudan-zvg/RealMotion) | 4 | ✅ working | `/raid/argoverse2` (present) | ✅ [RealMotion-I](https://drive.google.com/file/d/1MY4OfoEdoqFTdfDrHqcmo1pAUgUz1Gea/view) / [RealMotion](https://drive.google.com/file/d/1qyT0HHTMtpsvGy6YFo-jlp-1b-oNGbMr/view) | none stated |
| [TrajFlow](https://github.com/DSL-Lab/TrajFlow) | 5-6 | ✅ working, preprocessing verified | `/raid/waymo/scenario` — same missing plain `training` split gap as GameFormer; preprocessing verified against `validation`/`testing`/`*_interactive` splits, see [`TRAINING_PLAN.md`](docs/TRAINING_PLAN.md) | ❌ | MIT |
| [StreamingForecasting](https://github.com/ziqipang/StreamingForecasting) | 7 | ⏭️ not built (skipped) | Argoverse 1 (present) | ✅ VectorNet checkpoint | MIT |
| [emp](https://github.com/a-pru/emp) | 8 | ✅ working | `/raid/argoverse2` (present) | ✅ EMP-M / EMP-D bundled | BSD-3-Clause |
| [SceneInformer](https://github.com/sisl/SceneInformer) | 9 | ✅ working, training verified on GPU0 | `/raid/waymo/scenario` (present); stage 1 of the 4-stage preprocessing pipeline completed at full scale (1000 training + 150 validation shards); stages 2-4 not yet run at full scale — see [`TRAINING_PLAN.md`](docs/TRAINING_PLAN.md) | ❌ | MIT |
| [CMP](https://github.com/tasl-lab/CMP) | 10 | ✅ working | `/raid/datasets/OPV2V` + `/raid/datasets/V2V4Real` (present) | see repo's `docs/prepare_dataset_checkpoints.md` | none stated |
| [V2I_trajectory_prediction](https://github.com/xichennn/V2I_trajectory_prediction) | 11 | ⏭️ not built (skipped) | V2X-Seq (not present) | ❌ | none (all rights reserved by default) |
| [Pretraining-on-Synthetic](https://github.com/yhli123/Pretraining_on_Synthetic_Driving_Data_for_Trajectory_Prediction) | 12 | ✅ working | `/raid/argoverse1_1` + bundled synthetic set (present) | ✅ bundled in-repo (`pretrain/`, `finetune/`) | MIT |
| [UniAD](https://github.com/opendrivelab/uniad) | — (perception) | ✅ working | `/raid/nuscenes` (present) | ✅ Stage1 (perception) + Stage2 (planning), GitHub releases | Apache-2.0 |

"env only" = the Docker environment builds and passes `verify.sh`, but the dataset it
needs isn't on disk yet, so training/eval isn't runnable until that's fetched.

`StreamingForecasting` and `V2I_trajectory_prediction` were investigated (their
Dockerfile approach was scoped out) but not built, per an explicit scope decision — they
remain in `setup.sh --all` if wanted later.

## Data gaps

None remain. OPV2V and V2V4Real (needed by CMP) are done — 197GB and 41GB respectively
at `/raid/datasets/`, mounted into the `cmp` service. Waymo's `scenario` format
(needed by TrajFlow, SceneInformer, GameFormer, distinct from the `tf_example` format
also present) finished downloading to `/raid/waymo/scenario` (222GB, all 5 splits
confirmed complete: `training_20s`, `validation`, `testing`,
`validation_interactive`, `testing_interactive`) — no `docker-compose.yml` changes were
needed, those three services already mount the whole `/raid/waymo` directory. Each
repo's own preprocessing step is still required before training — see
[`docs/DATASETS.md`](docs/DATASETS.md) and [`docs/TRAINING_PLAN.md`](docs/TRAINING_PLAN.md).

## Training from scratch / running inference

General pattern: `docker compose run --rm <service> bash`, then follow that repo's own
README (present at `repos/<Name>/README.md` after `setup.sh`) — commands below are
copied from what's actually documented upstream, verified during this project's
build/test process:

```bash
# QCNet
docker compose run --rm qcnet bash -c "python train_qcnet.py --root /data/argoverse2 \
  --train_batch_size 4 --val_batch_size 4 --test_batch_size 4 --devices 1 \
  --dataset argoverse_v2 --num_historical_steps 50 --num_future_steps 60 \
  --num_recurrent_steps 3 --pl2pl_radius 150 --time_span 10 --pl2a_radius 50 \
  --a2a_radius 50 --num_t2m_steps 30 --pl2m_radius 150 --a2m_radius 150"
# Inference from a checkpoint: python val.py --model QCNet --root /data/argoverse2 --ckpt_path <path>

# RealMotion (Hydra-configured; edit repos/RealMotion/conf/ for the dataset path first)
docker compose run --rm realmotion bash -c "python train.py"
# python eval.py checkpoint=<path>

# emp
docker compose run --rm emp bash -c "python train.py data_root=/data/argoverse2 \
  model=emp gpus=1 batch_size=96 monitor=val_minFDE6 model.target.decoder=mlp"

# SceneInformer
docker compose run --rm sceneinformer bash -c "python scripts/train_lightning.py \
  --base configs/scene_informer.yaml -t"

# TrajFlow (from repos/TrajFlow/runner/)
docker compose run --rm trajflow bash -c "cd runner && bash scripts/dist_train.sh 4 \
  --cfg_file cfgs/waymo/trajflow+100_percent_data.yaml --epoch 40 --batch_size 80"

# UniTraj (bundles 6 backbones - method= selects which one)
docker compose run --rm unitraj bash -c "python train.py method=autobot"
```

For **GameFormer, UniAD, CMP, and Pretraining-on-Synthetic**, the exact flags weren't
double-checked as thoroughly during this project — get a shell and read that repo's own
README/`docs/` first (`docker compose run --rm <service> bash`, then `cat README.md`);
the environment is confirmed working, only the exact CLI invocation is left to the
repo's own documentation. UniAD in particular trains in two stages via scripts under
`tools/` — see `repos/UniAD/docs/`.

Checkpoints (where available, see the Status table) go through Google Drive links
in each repo's own README — download them yourself and mount or `docker cp` them into
the container, then pass the path via that repo's `--ckpt_path`/`checkpoint=`/similar
flag as shown above.

## Verifying everything works

```bash
./verify.sh                 # all 10 services
./verify.sh qcnet unitraj   # just these two
```

This isn't a model-correctness test — it's the same import+CUDA sanity check used
while originally building each image (torch/CUDA visible, key libraries importable,
compiled extensions loadable). A model actually training correctly is a separate,
much larger claim this script doesn't make.

## Adding a new repo

This is the exact recipe followed for all 10 repos here — expect real iteration
(rebuild, read the error, fix, repeat), not a one-shot process. Read
[`docs/BUILD_GOTCHAS.md`](docs/BUILD_GOTCHAS.md) first; the same handful of root causes
account for nearly every build failure hit so far.

1. `git clone --depth 1 <upstream-url> /tmp/scratch-clone` and read its README /
   `environment.yml` / `requirements.txt` to find the exact Python/PyTorch/CUDA pin it
   expects, and whether it compiles any custom CUDA extensions (`setup.py` importing
   `torch.utils.cpp_extension.CUDAExtension` is the tell).
2. `mkdir docker/<Name>` and write `docker/<Name>/Dockerfile`. Pick the closest existing
   template:
   - Pure pip, no custom CUDA ops → `docker/QCNet` or `docker/GameFormer`.
   - Compiles custom CUDA ops (knn/attention/etc.) → `docker/TrajFlow` or
     `docker/UniTraj`: needs a `cuda-toolkit` + matching `gcc`/`gxx` conda install (see
     gotchas), and an `entrypoint.sh` that builds the extension against the *mounted*
     source at container start rather than baking it into the image, so the repo stays
     live-editable. Copy `docker/TrajFlow/entrypoint.sh` as a starting point.
   - Repo ships its own official `docker/Dockerfile` → adapt it (see `docker/UniAD` and
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
8. Update the Status table above.

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
- [`docs/REPO_ASSESSMENT.md`](docs/REPO_ASSESSMENT.md) — which of these 10 are actually
  worth building on as a research baseline versus just useful for comparison, and what's
  missing from the shortlist entirely.
- **[Bearing & Bench](https://claude.ai/code/artifact/822a6791-32af-4d7e-8f69-ee138f1f16a6)**
  — a single-page read combining `REPO_ASSESSMENT.md` and `PHD_ROADMAP.md`, if that's
  easier to read in one sitting than two markdown files.
- [`docs/PHD_ROADMAP.md`](docs/PHD_ROADMAP.md) — how this benchmark fits into a 2-3 year
  PhD plan aimed at V2X motion forecasting.
