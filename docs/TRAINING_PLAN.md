# Training plan: getting real numbers out of every repo

Two different jobs, don't conflate them: **validating** a repo that already ships a
checkpoint (fast, minutes to ~1hr) versus **training from scratch** a repo that
doesn't (real compute commitment, hours to days). This doc is about the second one —
the actual work needed to get a first result out of each repo, and a sane order to
attempt it in given this machine has 2×24GB GPUs (RTX 3090 + 3090 Ti), where most of
these papers were trained on 4-8.

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

### 1. SceneInformer — start here

The original authors validated this on a single 24GB **TITAN RTX** — directly
comparable to your 3090s. Lowest risk of "doesn't fit" surprises.

```bash
docker compose run --rm sceneinformer bash -c "python scripts/train_lightning.py --base configs/scene_informer.yaml -t"
```

Needs the Waymo `scenario` data + its own preprocessing (`process_dataset.sh`) first —
see `docs/DATASETS.md`.

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
2 GPUs, halve the GPU count argument and reduce `--batch_size` proportionally (try 40,
watch GPU memory) rather than assuming it just works unmodified — this wasn't tested
at reduced scale this session, so treat the first run as a dry run to confirm it
doesn't OOM before trusting the results.

### 5. CMP — check for a checkpoint before assuming you need to train

The repo has a `docs/prepare_dataset_checkpoints.md` that wasn't fully read this
session — check it first; there may already be a checkpoint available, which would
move this into Track A instead. If not, per `REPO_ASSESSMENT.md`'s advice: a first
training run here is worth doing as a "does the pipeline actually train
end-to-end" technical check, separate from building your actual thesis contribution
on top of it (hold off on the latter until you've read its architecture properly).

## General GPU/batch-size adjustment

Most of these papers report results trained on 4-8 GPUs; this machine has 2. For any
of the above, if the default config OOMs or you want faster (if lower-fidelity) first
signal:

- Reduce `--batch_size`/`batch_size=` proportionally to GPU count, or use gradient
  accumulation if the training script supports it (check for an `accumulate_grad_batches`-
  style flag, common in PyTorch Lightning-based repos here).
- Reduce `--devices`/GPU-count flags to match what's actually available (`2`, not `4`
  or `8`).
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
