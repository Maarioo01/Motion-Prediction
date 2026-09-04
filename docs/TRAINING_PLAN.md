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

Download each checkpoint yourself (Google Drive links, manual — Drive throttles
scripted bulk downloads the same way Box did for OPV2V/V2V4Real), then either bind-mount
it into the container or `docker cp` it in.

## Track B — train from scratch (the real work)

No checkpoint exists, so this is the only way to get a number at all. Ordered
cheapest/lowest-risk to most demanding, based on what's actually known about each
repo's compute footprint — not a strict sequence, just where to start building
confidence before the heavier ones.

### 1. SceneInformer — done, verified end-to-end (small-scale)

The original authors validated this on a single 24GB TITAN RTX — directly comparable
to GPU0. This one is no longer theoretical: the full pipeline was run and a training
step actually executed successfully this session. Two real upstream bugs had to be
fixed first (both already patched in the live repo, see `BUILD_GOTCHAS.md` for
detail):

1. `sceneinformer/utils/waymo_utils.py` called `scenario.ParseFromString(bytearray(...))`,
   which modern `protobuf` rejects — patched to `bytes(...)`.
2. `configs/scene_informer.yaml` had literal unfilled `path: PATH` placeholders (train
   + validation) — now point at `/workspace/data_staging/occlusion`.
3. `scripts/train_lightning.py`'s `Trainer(...)` call had no `strategy=` set, which
   breaks under multi-GPU DDP given SceneInformer's decoder has branches not always
   used on every batch — patched to pass `strategy="ddp_find_unused_parameters_true"`
   when >1 device is requested. Moot for now (GPU1 disabled), but left in since it's
   the correct fix regardless.

**Preprocessing is a 4-stage pipeline**, and stage 2 is genuinely slow (the repo's own
README calls it out: "main computation is done here"):

```bash
# 1. Raw tfrecords -> pickled scenario lists
docker compose run --rm sceneinformer bash -c "python scripts/collect_raw_meas.py --src_path <raw_dir> --out_path <temp_dir> --n_cores 4"
# 2. Occlusion generation (slow - the repo's own README flags this as the main cost)
docker compose run --rm sceneinformer bash -c "python scripts/generate_occlusion_dataset.py --data_dir <temp_dir> --out_dir <out_dir> --n_cores 4"
# 3 & 4. Summary + index
docker compose run --rm sceneinformer bash -c "python scripts/generate_dataset_summary.py --data_path <out_dir>"
docker compose run --rm sceneinformer bash -c "python scripts/index_dataset.py --data_path <out_dir>"
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

**A small verified subset already exists** at `repos/SceneInformer/data_staging/`
(2.2GB: 4 training + 3 validation raw shards → ~1170 preprocessed scenario files) —
reuse this for a fast smoke test (`configs/scene_informer_smoketest.yaml`,
`val_check_interval: 5` instead of the real config's `10000`, appropriate for this
tiny sample) rather than rerunning the full pipeline every time you want to confirm
nothing's broken:

```bash
docker compose run --rm sceneinformer bash -c "python scripts/train_lightning.py --base configs/scene_informer_smoketest.yaml -t"
```

**For a real result**, rerun stages 1-4 above pointing at the full `training_20s`
(1000 shards) and `validation` (150 shards) directories instead of a small symlinked
subset, into a fresh output dir, then update `configs/scene_informer.yaml`'s `path:`
to match and run against that config (not the smoketest one) — expect stage 2 to take
considerably longer than the small-scale test did (proportionally, could be many
hours; wasn't measured at full scale this session, so budget generously and consider
running it as a detached background job rather than watching it).

### 2. GameFormer

No hard compute numbers were confirmed for this one this session — get a shell and
check `repos/GameFormer/README.md`'s training section before committing to a long run:

```bash
docker compose run --rm gameformer bash
# then: cd interaction_prediction && cat README.md  (or wherever the training script lives)
```

Needs the same Waymo `scenario` data + its own `data_process.py` preprocessing step.

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

The repo's own default recipe is explicitly **4-GPU**: `bash scripts/dist_train.sh 4
--cfg_file cfgs/waymo/trajflow+100_percent_data.yaml --epoch 40 --batch_size 80`. On
this machine's single usable GPU, set the device count to `1` and reduce `--batch_size`
proportionally (try 20, watch GPU memory) rather than assuming it just works
unmodified — this wasn't tested at reduced scale this session, so treat the first run
as a dry run to confirm it doesn't OOM before trusting the results.

### 5. CMP — check for a checkpoint before assuming you need to train

The repo has a `docs/prepare_dataset_checkpoints.md` that wasn't fully read this
session — check it first; there may already be a checkpoint available, which would
move this into Track A instead. If not, per `REPO_ASSESSMENT.md`'s advice: a first
training run here is worth doing as a "does the pipeline actually train
end-to-end" technical check, separate from building your actual thesis contribution
on top of it (hold off on the latter until you've read its architecture properly).

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
