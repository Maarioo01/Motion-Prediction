# Repo assessment: what's actually worth building on

An honest read on the 10 (+2 skipped) repos in this bench — not "does it build" (all 10
do), but "is it a good place to spend PhD time," and what's missing from the shortlist
given where the survey (`SURVEY_itss.pdf`) says the field's actual gaps are.

## The centerpiece: UniTraj, not any single model

If the goal is "test fast different approaches," **UniTraj is the actual answer**, more
than any single-model repo here. It isn't one baseline — it's a training/eval harness
that already bundles six backbones (AutoBot, MTR, Wayformer, SMART, Forecast-MAE, EMP)
behind one Hydra config system across four datasets (Waymo, nuPlan, nuScenes,
Argoverse2). A new idea that can be expressed as "modify one encoder/decoder module"
gets a fair multi-backbone, multi-dataset comparison almost for free, instead of
re-plumbing data loaders and eval scripts for every baseline separately — which is
exactly the kind of overhead that eats a first PhD year. Two real caveats: it's
**AGPLv3**, copyleft — worth checking your university's and any future publication
venue's stance on that before code tied to it goes into a public thesis-adjacent repo,
and it's a genuine framework (more moving parts, more places to hit a wall) rather than
a clean single paper implementation, which is a fair trade for what it buys.

## Strong, focused baselines

**QCNet** (rank 1, Apache-2.0) is the most credible reference point — genuinely SOTA on
both Argoverse leaderboards at publication, clean modern query-centric design, and
permissively licensed. Worth reproducing its reported numbers early, once, as a
competence checkpoint — "I can match a published SOTA number on this bench" is a good
thing to be able to say by the end of year 1.

**emp** (BSD-3, checkpoints bundled) is the opposite kind of asset: not SOTA, but
explicitly built to train in hours on one GPU. Good for the "I have an idea, let me see
if it moves a number by Friday" loop — the actual daily-driver for iterating on small
architectural changes, less useful as a paper's headline comparison.

**RealMotion, TrajFlow, SceneInformer, GameFormer** are all solid single-paper
implementations, useful as comparison numbers in a results table, less as a base to
extend unless the specific idea is inherently about their mechanism (RealMotion's
streaming two-stream design, TrajFlow's flow-matching, SceneInformer's occlusion
inference, GameFormer's game-theoretic joint prediction). None are copyleft-licensed
except where unstated (GameFormer has no license file at all — ask before reusing code
from it in anything released).

## The V2X-relevant two: promising but not ready yet

**CMP** is the one repo here that's directly a cooperative-prediction pipeline
(OpenCOOD detection + AB3Dmot tracking + MTR prediction), which matches the eventual
thesis direction — but it's also the least production-ready thing in the bench: pinned
to Python 3.7 (EOL, see `BUILD_GOTCHAS.md`) and no license stated. Its two datasets
(OPV2V, V2V4Real) are now downloaded (197GB + 41GB on `/raid/datasets/`, mounted into
the `cmp` service) — good to have working *and* fed *now*, still premature to build the
actual thesis contribution on top of until you've had a chance to read its architecture
properly.

**Pretraining-on-Synthetic** is a narrower, DenseTNT-lineage pretrain/fine-tune recipe
— useful less as a baseline to beat and more as a technique (synthetic-map
pretraining) that could transfer to a data-scarce V2X setting later, if real
cooperative data stays limited.

## The odd one out: UniAD

Full perception+prediction+planning stack, not a trajectory predictor in the sense the
other nine are. Genuinely excellent engineering (this survey's own Fig. 1 shows
raw-perception approaches are the minority of the field, and UniAD is one of the more
complete examples of one) but it's the heaviest thing here (Stage 1 needs ~30-50GB/GPU,
over what this machine's 24GB cards can do without model parallelism) and the least
aligned with the stated "without perception" framing. Keep it around as a reference for
how a full stack is structured — useful context if the thesis ever needs to reason
about what happens upstream of the prediction module — but it's not where year 1 or 2
effort should go.

## Skipped repos — worth reconsidering, not dismissed

`StreamingForecasting` and `V2I_trajectory_prediction` were investigated but not built
(scope decision, not a quality judgment). `V2I_trajectory_prediction` in particular is
literally reference [12] in the survey — the only *other* corpus paper besides CMP's
[89] that uses a cooperative dataset (V2X-Seq), and it's a light, standalone model
(conformal-prediction wrapper over a base trajectory predictor), unlike CMP's heavy
three-module pipeline. If the V2X direction firms up, this is probably a cheaper second
data point than it looked at first glance — `./setup.sh --all` still fetches it, the
Docker environment just was never built. Given it ships with essentially no
environment spec at all in the repo, expect to reconstruct its dependencies from
scratch the way `V2I`'s scope-out notes already describe.

## What's missing from the shortlist entirely

The survey's own Section VI is the honest list of gaps, and this 12-repo shortlist
inherits all of them since it was drawn directly from the survey's corpus:

- **No cooperative-perception-specific architecture repos beyond CMP/V2I.** The wider
  literature has other well-known cooperative-fusion designs (e.g. Where2comm, CoAlign,
  V2X-ViT, HEAL — not in the survey's corpus, so not in this shortlist either) that are
  worth a literature scan once the V2X phase starts, specifically for how they handle
  *communication-efficient* fusion, which is the open problem CMP's own related-work
  section frames.
- **No calibration/regret-aware evaluation code.** Section VI.A's gap (distance metrics
  reward proximity to one ground truth, not calibrated confidence) has no
  implementation in this bench at all — [60]'s Regret metric and [92]'s OOD/uncertainty
  work are cited in the survey but neither repo was in scope for this project. If a
  first paper needs a fast, low-risk empirical angle, implementing one of these on top
  of an existing baseline here (QCNet or emp) and reporting how rankings change is
  cheap to run and directly extends work the survey already frames as underexplored.
  See `PHD_ROADMAP.md`.
- **No cross-topology/cross-city generalization harness.** Section VI.D's gap
  ([4]'s finding that predictors degrade sharply on perturbed road topology) also has
  no repo here — but it's cheap to construct standalone (perturb existing AV2/Waymo map
  data, no new dataset needed) rather than requiring a whole new repo.
- **No LLM-backbone repos.** Section V.D's emerging LLM-for-forecasting direction
  (CoT-Drive, GPT-Driver, LC-LLM) isn't represented — reasonable to leave out for now
  given the V2X focus, but worth knowing it's a live sub-area if the thesis direction
  shifts toward explainability later (Section VI.E's other named gap).

None of these need to become part of this Docker bench immediately — flagging them here
so the gap between "what's built" and "what the survey says the field is missing" stays
visible rather than silently forgotten once the bench itself is running.
