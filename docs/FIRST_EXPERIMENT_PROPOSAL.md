# First experiment proposal: confidence-aware, permutation-invariant prediction aggregation for CMP

Status: **proposal, not started**. Written up so the idea survives past one conversation —
see [`REPO_ASSESSMENT.md`](REPO_ASSESSMENT.md) and [`PHD_ROADMAP.md`](PHD_ROADMAP.md) for
how this fits the broader plan, and [`MODELS_OVERVIEW.md`](MODELS_OVERVIEW.md) for the
CMP/MTR background this builds on.

## Why this, why now

Two independent things pointed at the same gap:

1. **Reading CMP's actual code** (`repos/CMP/MTR/mtr/models_opv2v/multi_ego_mtr_model.py`)
   turned up something concrete. CMP's Prediction Aggregation Module — the one genuinely
   novel piece of its pipeline — has **14 different aggregator implementations** coded
   (MLP, MLPV2, GCN, six MOE variants, two Transformers), clear evidence of heavy
   experimentation. The one actually used in the released checkpoint (confirmed via
   `tools/cfgs/opv2v/opv2v_multiego_cobevt_c256.yaml`'s `MOTION_AGGREGATOR.TYPE: 'Transformer'`)
   is `MotionAggregatorTransformer`. It defines a proper query-based cross-attention
   decoder meant to reduce a variable number of contributing CAVs' predictions down to a
   fixed K=6 output (`self.transformer_decoder`, 6 learnable query tokens) — **and never
   calls it**. The line is commented out (`# modes_of_embeddings = self.transformer_decoder(...)`).
   Instead, the actual reduction is `agent_feature_embeddings_transformed[:num_modes, :512]`
   — a plain slice of the first K rows after self-attention. That's not permutation-invariant:
   the result depends on the arbitrary order the contributing CAVs' embeddings were
   concatenated in, which isn't principled multi-agent fusion.
2. **A literature search** (Sept 2026) specifically for papers that treat per-agent
   detection confidence, communication latency, or occlusion as *explicit prediction-stage
   input features* — rather than baking them into the fusion architecture the way every
   existing cooperative-perception paper does — found **none**. Closest prior art: MSMA
   (Chen/Bhadani/Head, arXiv 2407.21310) tests robustness under synthesized noise/latency
   as an *evaluation condition*, not as a feature the model conditions on. CooperTrim and
   UECP do confidence-weighted fusion, but at the perception stage, and the confidence
   signal is used internally for weighting rather than exposed as an explicit input. CMP
   itself doesn't use per-CAV confidence anywhere in its aggregation step at all — every
   contributing CAV's prediction is currently treated as equally reliable.

Both point at the same fix, from different directions: **CMP's aggregation step is neither
properly permutation-invariant nor confidence-aware**, and nobody else in the current
literature has closed that gap either. That's the basis for this proposal.

## What NOT to do

This is explicitly *not* a new architecture. It's a targeted intervention in one module of
an existing, already-validated pipeline, evaluated with a clean ablation. Keep the
detection stage (CoBEVT), tracking stage (AB3DMOT), and the per-CAV MTR prediction stage
completely unchanged — only the aggregation module changes. That's what keeps this small
and keeps the before/after comparison attributable to one thing.

## Proposed changes, as two separable ablation arms

**Arm A — fix permutation-invariance (cheapest, do this first).**
Replace the naive slice with either:
- the query-based decoder that's already written but disabled (uncomment and wire up
  `self.transformer_decoder(self.query_embeddings, agent_feature_embeddings_transformed)`,
  which was clearly the original intent), or
- a simpler, even cheaper permutation-invariant pool (max- or mean-pool over the
  contributing-CAV dimension before the final projection) as a lower-effort alternative if
  the decoder route turns out to need more surgery than expected.

This alone is a legitimate, self-contained finding regardless of Arm B: does fixing the
non-determinism/order-dependence already in CMP's own design measurably change
minADE/minFDE, holding everything else fixed?

**Arm B — confidence-weighted aggregation (the more novel piece).**
Weight each contributing CAV's trajectory embedding by that CAV's own detection confidence
for the specific target agent, before or during the self-attention step — e.g. as an
additive attention bias, or concatenated as an extra scalar feature into
`self.feature_encoder`'s input alongside the trajectory. Two open questions to resolve
before implementing, not yet investigated:
- **Where does per-box detection confidence actually live in the pipeline's saved
  output?** Need to check OpenCOOD's detection head (`repos/CMP/opencood/models/`) for
  whether a per-box score survives through to what `multi_ego_mtr_model.py` receives, or
  whether it needs to be threaded through from an earlier stage.
- **What should "confidence" mean for a CAV's prediction of an agent it can only see
  indirectly through a teammate's shared features?** Detection confidence and prediction
  reliability aren't the same thing — this needs a clear, defensible definition before
  it's a feature, not just "whatever score happens to be lying around."

## Evaluation plan

Same protocol CMP's own paper uses, so results are directly comparable to the numbers
already in `MODELS_OVERVIEW.md`: minADE₆/minFDE₆ at 1s/3s/5s, on both OPV2V and
V2V4Real (both already downloaded, see `DATASETS.md`).

| Row | Detection | Tracking | Prediction | Aggregation | Expected purpose |
|---|---|---|---|---|---|
| 1 | CoBEVT | AB3DMOT | MTR | **CMP as released** (naive slice) | baseline, reproduce the checkpoint's own numbers first |
| 2 | CoBEVT | AB3DMOT | MTR | **Arm A** (fixed pooling) | isolates the permutation-invariance fix alone |
| 3 | CoBEVT | AB3DMOT | MTR | **Arm A + B** (fixed pooling + confidence) | the actual proposed contribution |

Rows 2 and 3 need to be genuinely separable in the write-up — if B helps, the paper needs
to show A alone *didn't* already capture the whole effect, otherwise the confidence
weighting isn't shown to be doing anything.

## Relation to recent literature (as of the Sept 2026 search)

Situates the idea against what's actually out there right now, not what the original
survey covered:
- **CoPAD** (arXiv 2509.15984), **Co-MTP** (arXiv 2502.16589), **V2X-RECT** (arXiv
  2511.17941), **CAMNet** (arXiv 2510.12703) are the closest recent competitors —
  all fusion-architecture variants on V2X-Seq, none touch confidence/latency as an
  explicit input feature.
- **"Collaborative Trajectory Prediction via Late Fusion"** (arXiv 2604.22973, Apr 2026)
  is a direct critique of CMP's whole design philosophy — argues early/intermediate
  fusion (what CMP does) assumes unrealistic bandwidth/sync, proposes fusing independent
  per-vehicle forecasts instead, evaluated on the same OPV2V/V2V4Real data this project
  already has. **Read this before writing anything** — if confidence-weighting makes
  CMP-style fusion more robust to exactly the kind of unreliability that paper is
  criticizing, that's a stronger, more citable narrative than treating it as unrelated
  work.
- **V2XPnP-Seq** (arXiv 2412.01812, ICCV 2025) and **CAMASA** (arXiv 2606.10641, real
  V2X message logs) are newer datasets that could matter for a *follow-up* validation
  once the OPV2V/V2V4Real result exists, particularly CAMASA for testing under real
  (not simulated) message loss/latency — not needed to start.

## Honest risks

- The improvement might be small, or might wash out once Arm A alone is isolated —
  that's a real, useful negative result either way, not a reason to not run the
  experiment.
- Per-box confidence might not be cleanly available without rerunning the detection
  stage — first investigation step, before writing any aggregator code.
- A reviewer familiar with the Late-Fusion critique paper may ask why extend
  early/intermediate fusion at all rather than adopt late fusion — worth having an answer
  ready (e.g., "confidence-aware early fusion vs. late fusion" as a comparison, not just
  CMP-vs-CMP+ours).

## Rough scope

This is meant to be small. A realistic first pass: confirm the baseline checkpoint's
numbers reproduce (Track A, already partly done), implement and validate Arm A alone
(days, not weeks — it's largely uncommenting and wiring up existing code), then Arm B
(the confidence-source investigation is the real unknown-effort part). Not a full
semester's work by design.
