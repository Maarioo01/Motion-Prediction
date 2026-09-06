# Training plan: getting real numbers out of every repo

Two different jobs, don't conflate them: **validating** a repo that already ships a
checkpoint (fast, minutes to ~1hr) versus **training from scratch** a repo that
doesn't (real compute commitment, hours to days). This doc is about the second one —
the actual work needed to get a first result out of each repo, and a sane order to
attempt it in given this machine effectively has **one** usable 24GB GPU (GPU0, an
RTX 3090 - the second card, a 3090 Ti, is unreliable and disabled by policy, see the
README's "GPU allocation" section), where most of these papers were trained on 4-8.

## Track A — checkpoint validation (do these first, they're cheap)

Confirms the environment reproduces a *known* number before you trust it on anything
that doesn't have one to check against.

| Repo | Checkpoint | What to run |
|---|---|---|
| QCNet | [AV2 marginal](https://drive.google.com/file/d/1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv/view) | `python val.py --model QCNet --root /data/argoverse2 --ckpt_path <path>` |
| RealMotion | [RealMotion-I](https://drive.google.com/file/d/1MY4OfoEdoqFTdfDrHqcmo1pAUgUz1Gea/view) / [RealMotion](https://drive.google.com/file/d/1qyT0HHTMtpsvGy6YFo-jlp-1b-oNGbMr/view) | `python eval.py checkpoint=<path>` |
| emp | bundled (EMP-M / EMP-D) | `python eval.py data_root=/data/argoverse2 batch_size=32 'checkpoint="<path>"'` |
| Pretraining-on-Synthetic | bundled in `pretrain/`, `finetune/` | see the repo's own `bash/` scripts — didn't verify the exact eval command this session |
| UniAD | Stage1 + Stage2, GitHub releases | two-stage, via `tools/` — see `repos/UniAD/docs/`, didn't verify exact commands this session |
| CMP | [perception ckpts](https://drive.google.com/drive/folders/1EizY6ZFMi__HnqeFPQ2Wf9yRJeD_-S82) (CoBEVT/V2VNet, both OPV2V+V2V4Real) + [prediction ckpts](https://drive.google.com/drive/folders/1ZUJ5a5VuNfxV34I9FmIefHDGixaJ7gM2) (4 variants each: no-coop, coop-perception-only, full CMP, V2VNet baseline) | see `repos/CMP/docs/prepare_dataset_checkpoints.md` for the exact `pretrained/`/`MTR/output/` folder layout each checkpoint set expects — this was missed in the first pass through the repos and moves CMP out of Track B entirely |

Download each checkpoint yourself (Google Drive links, manual — Drive throttles
scripted bulk downloads the same way Box did for OPV2V/V2V4Real), then either bind-mount
it into the container or `docker cp` it in.

## Track B — train from scratch (the real work)

No checkpoint exists, so this is the only way to get a number at all. Ordered
cheapest/lowest-risk to most demanding, based on what's actually known about each
repo's compute footprint — not a strict sequence, just where to start building
confidence before the heavier ones.

### 1. SceneInformer — done, real training running on GPU0

The original authors validated this on a single 24GB TITAN RTX — directly comparable
to GPU0. This is no longer a smoke test: the full 4-stage pipeline ran at full scale
(1000 training + 150 validation Waymo `training_20s`/`validation` shards) and real
training is now underway. Four real upstream bugs had to be fixed first (all patched
in the live repo via `docker/SceneInformer/patches/` — see `BUILD_GOTCHAS.md` for
detail on each):

1. `sceneinformer/utils/waymo_utils.py` called `scenario.ParseFromString(bytearray(...))`,
   which modern `protobuf` rejects — patched to `bytes(...)`.
2. `configs/scene_informer.yaml` had literal unfilled `path: PATH` placeholders (train
   + validation) — now point at `/workspace/data_staging/occlusion_full`.
3. `scripts/train_lightning.py`'s `Trainer(...)` call had no `strategy=` set, which
   breaks under multi-GPU DDP given SceneInformer's decoder has branches not always
   used on every batch — patched to pass `strategy="ddp_find_unused_parameters_true"`
   when >1 device is requested. Moot for now (GPU1 disabled), but left in since it's
   the correct fix regardless.
4. `scripts/generate_dataset_summary.py` used `obj_idx` as a fancy array index without
   casting it to `int()` first (unlike `occluding_object_id` two lines below, which
   already did) — silent in the vast majority of files since the underlying array
   happens to be `int64`-typed almost everywhere, but `float64` in a rare few, which
   crashed numpy's fancy indexing. Found by scanning all 114638 stage-2 output files
   in parallel; only 2 actually hit it.

**Preprocessing is a 4-stage pipeline**, and stage 2 is genuinely slow (the repo's own
README calls it out: "main computation is done here" — took ~6 hours at full scale on
this machine's 16 cores, much longer than a naive extrapolation from the first few
shards suggested):

```bash
# 1. Raw tfrecords -> pickled scenario lists
docker compose run --rm sceneinformer bash -c "python scripts/collect_raw_meas.py --src_path <raw_dir> --out_path <temp_dir> --n_cores 16"
# 2. Occlusion generation (slow - the repo's own README flags this as the main cost)
docker compose run --rm sceneinformer bash -c "python scripts/generate_occlusion_dataset.py --data_dir <temp_dir> --out_dir <out_dir> --n_cores 16"
# 3 & 4. Summary + index (check the exit code directly - see the "pipe to tail" gotcha in BUILD_GOTCHAS.md)
docker compose run --rm sceneinformer bash -c "python scripts/generate_dataset_summary.py --data_path <out_dir>"; echo "exit: $?"
docker compose run --rm sceneinformer bash -c "python scripts/index_dataset.py --data_path <out_dir>"; echo "exit: $?"
```

`<raw_dir>` needs `training/` and `validation/` subdirectories directly containing raw
tfrecords — note the actual Waymo folder is named `training_20s`, not `training`
(`collect_raw_meas.py` hardcodes the latter), so symlink around the mismatch rather
than renaming the real (read-only-mounted) data:
```bash
mkdir -p <raw_dir>/training <raw_dir>/validation
ln -s /data/waymo/scenario/training_20s/<file> <raw_dir>/training/<file>   # per file, or a loop
ln -s /data/waymo/scenario/validation/<file> <raw_dir>/validation/<file>
```

**A small verified subset still exists** at `/raid/scratch/sceneinformer_data_staging/`
(`raw`/`temp`/`occlusion` — the small toy set; `raw_full`/`temp_full`/`occlusion_full`
are the full-scale run) — reuse the toy one for a fast smoke test
(`configs/scene_informer_smoketest.yaml`, `val_check_interval: 5`) rather than
rerunning the full pipeline every time you want to confirm nothing's broken. Note:
`data_staging/` for this and the other Waymo-preprocessing repos (GameFormer,
TrajFlow) is bind-mounted from `/raid/scratch/<name>_data_staging`, **not** stored
under `repos/<Name>/` directly — see the "repos/ lives on the OS disk" gotcha in
`BUILD_GOTCHAS.md` for why.

**Real training is running**: full-scale preprocessing produced 70541 training / 44097
validation samples (`VectorizedDatasetHDF5`, batch_size 10 → 7055 batches/epoch — much
smaller than a naive per-occlusion-event sample count would suggest, since the dataset
wraps the raw positive/negative index arrays into fixed windows; had to drop
`val_check_interval` from 10000 to 2000 once the real batch count was known, same
class of error as the original toy-dataset mismatch, just discovered at a different
scale). Launched as a **detached** container (`docker compose run -d --rm sceneinformer
...`, not tracked as a foreground/backgrounded shell task) specifically so a long
training run survives independently of any one session — confirmed running on GPU0
(97% util, ~12GB VRAM) with GPU1 untouched:

```bash
docker compose run -d --rm sceneinformer bash -c "python scripts/train_lightning.py --base configs/scene_informer.yaml -t > /workspace/train_full.log 2>&1"
# find it: docker ps --filter name=sceneinformer
# watch it: docker exec <container> tail -f /workspace/train_full.log
```

### 2. GameFormer

Preprocessing (`interaction_prediction/data_process.py`) is verified working — but only
against the **plain `training`/`validation`/`testing` Waymo split, not `training_20s`**
(the one downloaded for SceneInformer). The two splits are different scenario
populations: `training_20s` has `tracks_to_predict` always empty, which is what
`data_process.py` keys off, so it crashed with `KeyError: <id>` on `training_20s` (a
real upstream bug, patched — see `BUILD_GOTCHAS.md` and
`docker/GameFormer/patches/data_process.py`) and, after the crash-fix, silently produces
**zero output** on `training_20s` regardless. Confirmed the fix and the pipeline both
work correctly against the real `validation` split instead: 3 shards → 7403
correctly-shaped `.npz` files.

```bash
docker compose run --rm gameformer bash -c "cd interaction_prediction && python data_process.py --load_path <raw_dir> --save_path ../data_staging/processed --use_multiprocessing --processes 16"
```

**The plain `training` split (1000 shards) is not yet downloaded** (`/raid/waymo/scenario`
only has `training_20s`, `validation`, `testing`, `validation_interactive`,
`testing_interactive`) — needed before a real training run, same gap as TrajFlow below.
See `DATASETS.md` for the `gsutil` command once re-authenticated.

### 3. UniTraj — do the smoke test first, separately from real training

```bash
docker compose run --rm unitraj bash -c "python train.py method=autobot"
```

This trains on a tiny bundled sample in minutes — it's a smoke test that the
environment/pipeline works, **not a real result**. For an actual number, point it at
real data via ScenarioNet (not yet converted — see the "ScenarioNet conversion not
run" note in the main README's status table) and expect real training time. Since it's
one harness across 6 backbones, once ScenarioNet conversion is done once, getting a
second backbone's number is just `method=mtr` / `method=wayformer` / etc. — cheap
incrementally even though the first setup isn't.

### 4. TrajFlow

Preprocessing (`trajflow/datasets/waymo/data_preprocess.py`) is verified working —
tested against a small staged subset covering all 5 expected subfolders
(`training`/`validation`/`testing`/`validation_interactive`/`testing_interactive`).
Unlike SceneInformer, its `ParseFromString(bytearray(...))` call doesn't hit the
protobuf bug (this image's protobuf 3.20.3 still accepts `bytearray`, only newer
protobuf rejects it). It handles a missing/empty split gracefully (an empty `training/`
folder just yields 0 infos, no crash) rather than erroring, which is how the same
**missing plain `training` split** gap as GameFormer above was confirmed here too — the
existing `validation`/`testing`/`*_interactive` splits process correctly (right shapes,
right file layout), but a real training run needs the still-undownloaded `training`
split.

```bash
docker compose run --rm trajflow bash -c "cd trajflow/datasets/waymo && python data_preprocess.py <raw_data_path> ../../../data_staging/processed"
```

`<raw_data_path>` needs `training/`, `validation/`, `testing/`, `validation_interactive/`,
`testing_interactive/` subdirectories directly containing the matching raw tfrecords
(symlink from `/data/waymo/scenario/<split>/` per file, same pattern as SceneInformer).

The repo's own default training recipe is explicitly **4-GPU**: `bash
scripts/dist_train.sh 4 --cfg_file cfgs/waymo/trajflow+100_percent_data.yaml --epoch 40
--batch_size 80`. On this machine's single usable GPU, set the device count to `1` and
reduce `--batch_size` proportionally (try 20, watch GPU memory) rather than assuming it
just works unmodified — this wasn't tested at reduced scale this session, so treat the
first run as a dry run to confirm it doesn't OOM before trusting the results.

### 5. CMP — has checkpoints, moved to Track A

Checked `docs/prepare_dataset_checkpoints.md`: CMP ships both perception checkpoints
(CoBEVT/V2VNet, both datasets) and prediction checkpoints (4 variants: no-cooperation,
cooperative-perception-only, the full CMP model, and a V2VNet baseline — useful
ablations already done for you), all via Google Drive — see the Track A table above.
Nothing to train from scratch here unless you want to reproduce the paper's numbers
yourself rather than validate against them. Once validated, per `REPO_ASSESSMENT.md`'s
advice: treat a first training run as a "does the pipeline train end-to-end" technical
check, separate from building your actual thesis contribution on top of it (hold off on
the latter until you've read its architecture properly).

## General GPU/batch-size adjustment

Most of these papers report results trained on 4-8 GPUs; this machine effectively has
**1** usable GPU (see the README's "GPU allocation" section — GPU1 is unreliable and
disabled by policy). For any of the above, if the default config OOMs or you want
faster (if lower-fidelity) first signal:

- Reduce `--batch_size`/`batch_size=` proportionally to GPU count, or use gradient
  accumulation if the training script supports it (check for an `accumulate_grad_batches`-
  style flag, common in PyTorch Lightning-based repos here).
- Reduce `--devices`/GPU-count flags to `1` everywhere - don't request GPU1 or an
  "all GPUs" setting in any repo's own config, for the same reason `docker-compose.yml`
  pins every service to `device_ids: ["0"]`.
- Don't expect an exact paper-matching number on a reduced-scale first run — the
  realistic near-term goal is "does it converge and produce a sane minADE/minFDE
  trend," not "matches Table 3 of the paper." Full-scale reproduction, if wanted, is a
  separate, longer effort once you've confirmed the pipeline itself works.
- Watch for `wandb`/`tensorboard` logging already wired into most of these (several
  pull in `wandb` as a dependency) — use it rather than eyeballing stdout loss values,
  it's already there.

## After a first training run

For each repo that trained successfully, add its resulting minADE/minFDE (or whatever
metric it reports) back into `REPO_ASSESSMENT.md` or a new results table — this doc is
about getting the run to happen, not about tracking outcomes once you have them.
