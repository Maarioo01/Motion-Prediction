# CLAUDE.md — Motion-Prediction (V2X PhD bench)

Instructions for Claude Code sessions on Mario's workstation. Read this first, then the
plan documents below before doing any work.

## Who and what

- **Mario** is a PhD student. His thesis is **100 % V2X motion prediction** (vehicle +
  infrastructure / vehicle-to-vehicle cooperative trajectory forecasting).
  **Talk to him in Spanish**, without heavy jargon. Write code, commits and repo docs in English,
  except the Spanish plan documents in `docs/v2x_plan/`.
- This repo is a **Docker benchmark bench**: one Docker image per upstream model repo,
  shared datasets on `/raid`, GPU0 only. Upstream code lives in `repos/` (gitignored,
  recreated by `setup.sh`); this repo tracks only `docker/<Name>/`, `docker-compose.yml`,
  `setup.sh`, `verify.sh` and `docs/`.

## Plan documents (source of truth)

| File | What it is |
| --- | --- |
| [`docs/v2x_plan/PHASE0_CHECKLIST.md`](docs/v2x_plan/PHASE0_CHECKLIST.md) | **The current task list.** Work from it; tick items with date + note. |
| [`docs/v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md`](docs/v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md) | Full report (Spanish) — the *why*. Section 12 is the roadmap; 7.2 the training decisions; 10 the benchmark design. |
| [`docs/v2x_plan/PAPER1_V2X_BENCHMARK.md`](docs/v2x_plan/PAPER1_V2X_BENCHMARK.md) | One-page summary of paper 1 (unified V2X benchmark). |
| [`docs/FIRST_EXPERIMENT_PROPOSAL.md`](docs/FIRST_EXPERIMENT_PROPOSAL.md) | CMP aggregation fix (Arm A = warm-up only). |
| [`docs/BUILD_GOTCHAS.md`](docs/BUILD_GOTCHAS.md) | Read before adding any new repo/Docker image. |
| [`docs/PHD_ROADMAP.md`](docs/PHD_ROADMAP.md) | **Superseded** (kept for history). Do not plan from it. |

## Standing decisions (2026-11-09)

1. **Real datasets only.** No simulated or synthetic data (OPV2V, CARLA-based sets, the
   Pretraining-on-Synthetic bundle). Do not propose them.
2. **ZARAGOZA-V2X is out of scope** — never reference or use it.
3. **First paper = unified V2X benchmark** (V2X-Seq-TFD + V2X-Traj, V2V4Real as V2V extra):
   one protocol, multiple seeds, no privileged information, plus calibration, communication
   robustness, cost, and per-difficulty/occlusion analysis.
4. Default model family for our own work: **relative / query-centric** (HiVT/QCNet style),
   propose → refine decoder, calibrated mode probabilities.

## Methods

Active (keep in `setup.sh` + `docker-compose.yml`):

| Service | Why |
| --- | --- |
| QCNet | Base for our own model; to be adapted to V2X-Seq. AV2 checkpoint for sanity checks. |
| CMP | Only cooperative pipeline in the bench; V2V4Real only; aggregation-fix warm-up. |
| *to add:* V2X-Graph, V2INet (`V2I_trajectory_prediction`), Co-MTP, HiVT | The V2X baselines for paper 1 (see checklist B2–B5). |

Archived (moved to `docker/_archive/<Name>/`, removed from `setup.sh` and
`docker-compose.yml`; do not build or run them unless Mario asks):
UniTraj, GameFormer, TrajFlow, MTR, SceneInformer, RealMotion, emp, pretraining-synthetic,
UniAD. (RealMotion may come back for the streaming idea of paper 2; StreamingForecasting stays
unbuilt.)

## Datasets (`/raid`)

| Path | Status |
| --- | --- |
| `/raid/datasets/V2X-Seq-TFD` | **To download** (checklist A1). |
| `/raid/datasets/V2X-Traj` | **To download** (checklist A2). |
| `/raid/datasets/V2V4Real` | Keep (real V2V; CMP). |
| `/raid/argoverse2` | Keep (QCNet pretraining / checkpoint validation). |
| `/raid/waymo/scenario` (plain `training`, `validation`, `testing`, interactive splits) | Keep (Mario's choice). |
| `/raid/nuscenes` | Keep for now (needed by the GaussianCaR collaboration, which uses nuScenes). |
| `/raid/datasets/OPV2V` | Delete (simulated). |
| `repos/pretraining-synthetic` bundled synthetic set | Delete with the archived repo. |
| `/raid/waymo/scenario/training_20s` | Delete candidate (only SceneInformer used it). |
| `/raid/argoverse1_1` | Delete candidate (only archived repos used it). |
| `/raid/scratch/*_data_staging` (trajflow, mtr, gameformer, sceneinformer) | Delete (other models' preprocessing). |

Keep [`docs/DATASETS.md`](docs/DATASETS.md) and the README status table in sync with
what is actually on disk.

## Safety rules

- **Never delete data or kill processes without an explicit "yes" from Mario in this
  session.** Before any deletion: list each path with `du -sh`, say what uses it, and wait.
  Check `docker ps`, `nvidia-smi` and running processes first; a training run (e.g.
  SceneInformer) may still be using a path.
- Archive configs with `git mv`, never `rm`.
- **GPU0 only** (`device_ids: ["0"]`). Never request GPU1 or `all` (see README, "GPU allocation").
- Mount datasets read-only; write preprocessing output under `/raid/scratch/<name>_*`, not
  the OS disk.
- For every reported number record: upstream commit (`git -C repos/<Name> rev-parse HEAD`),
  config, seed, split. A number without these does not go into the benchmark.
- Don't download behind a login, license click-through or application form on Mario's
  behalf: prepare the steps and let him do that part.
- Work on a branch and open a PR for repo changes. Commit messages and docs in English.

## Common commands

```bash
git pull                       # always start here
./setup.sh                     # clone/overlay active upstream repos into repos/
docker compose build <service> # build one image
./verify.sh <service>          # import + CUDA sanity check
docker compose run --rm <service> bash
```
