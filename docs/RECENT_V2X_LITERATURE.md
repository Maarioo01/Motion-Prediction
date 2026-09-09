# Recent V2X motion-forecasting literature (as of a Sept 2026 search)

Captures a literature search run mid-project to check whether cooperative motion
forecasting is still the underexplored niche the survey (`SURVEY_itss.pdf`) found it to
be, and specifically whether anyone has already done the confidence/latency/occlusion
input-featurization idea in [`FIRST_EXPERIMENT_PROPOSAL.md`](FIRST_EXPERIMENT_PROPOSAL.md).
Written down so it isn't lost to one conversation — cite this doc rather than re-deriving
it, and re-run the search periodically since this field is moving fast.

## New cooperative motion-forecasting papers (roughly the last 12-18 months)

- **CoPAD** (arXiv 2509.15984, Sept 2025) — Hungarian+Kalman early fusion of
  multi-source trajectories, "Past Time Attention" + anchor-oriented decoder. DAIR-V2X-Seq,
  ~12-13% error reduction over baselines. Same family as CMP but trajectory-only, no raw
  perception fusion.
- **ViTraj** (ACM MM 2025) — dual-side vehicle-infrastructure representations. No public
  arXiv preprint found — underverified beyond the ACM listing.
- **V2XPnP** (arXiv 2412.01812, ICCV 2025, UCLA Mobility Lab) — unified Transformer doing
  perception *and* prediction jointly, benchmarks early/late/intermediate fusion x
  one-step/multi-step communication across 11 SOTA fusion models. Ships a new dataset
  (V2XPnP-Seq, see below) — significant, worth reading in full.
- **TurboTrain** (arXiv 2508.04682, ICCV 2025, same UCLA group) — training framework
  (masked-reconstruction pretraining + gradient-conflict-suppression multi-task learning),
  not a new architecture. Evaluated on V2XPnP-Seq.
- **CAMNet** (arXiv 2510.12703, CCNC 2026) — builds a GNN directly on standardized V2V
  Cooperative Awareness Messages (position/motion/status broadcasts) instead of fusing raw
  LiDAR/perception features like CMP. Trained on a standard forecasting dataset, evaluated
  on a real CAM dataset they built. Doesn't model message loss/latency/confidence as inputs.
- **V2X-RECT** (arXiv 2511.17941, Nov 2025) — targets ID-switch/tracking-association
  errors corrupting cross-view fusion in dense traffic; treats imperfect cooperative
  *tracking* as a noise source to correct before prediction (adjacent to, but framed as
  error-correction rather than as a feature, the confidence-featurization idea).
- **Collaborative Trajectory Prediction via Late Fusion** (arXiv 2604.22973, Apr 2026) —
  **read this one before extending CMP.** Argues CMP-style early/intermediate feature
  fusion "assumes idealized bandwidth and synchronization" and incurs substantial
  communication overhead; proposes model-agnostic late fusion of independent per-vehicle
  forecasts instead. Evaluated on OPV2V, V2V4Real, *and* DeepAccident. A direct critique of
  the design `FIRST_EXPERIMENT_PROPOSAL.md` builds on.
- **V2V-LLM** (arXiv 2502.09980, ICRA 2026) and **V2V-GoT** (arXiv 2509.18053, Sept 2025) —
  MLLM-mediated cooperation: CAVs share features with a shared multimodal LLM handling
  perception+prediction+planning QA jointly. V2V-GoT adds graph-of-thoughts reasoning,
  occlusion-aware perception, "planning-aware prediction." Ships a large QA dataset
  (110K/31K train/test). A genuinely different paradigm from fusion-architecture papers.
- **Co-MTP** (arXiv 2502.16589, Feb 2025) — multi-temporal fusion (history *and* future
  interaction), heterogeneous graph transformer, currently SOTA on V2X-Seq.
- **I2XTraj** (arXiv 2501.13461, Jan 2025) — knowledge-informed prediction at signalized
  intersections using traffic-signal state; V2X-Seq and SinD.

## Newer/larger V2X cooperative-prediction datasets

- **V2XPnP-Seq** (arXiv 2412.01812, [GitHub](https://github.com/Zewei-Zhou/V2XPnP), ICCV
  2025) — **the most important one to know about.** Real-world, first to support all four
  V2X collaboration modes (Vehicle-Centric, Infrastructure-Centric, V2V, I2I) in one
  dataset, vs. V2X-Seq's single vehicle-infrastructure mode. Purpose-built for joint
  perception+prediction benchmarking — arguably more aligned to "cooperative
  perception-and-prediction" than V2X-Seq is.
- **UrbanIng-V2X** (arXiv 2510.23478, NeurIPS 2025,
  [GitHub](https://github.com/thi-ad/UrbanIng-V2X)) — 2 vehicles + up to 3 infrastructure
  sensor poles across 3 real Ingolstadt intersections, ~712K annotated 3D instances, 13
  classes, 10Hz. Supports detection/tracking/localization *and* prediction, but reads as
  primarily a perception-benchmark dataset with prediction as one of several downstream
  tasks, not prediction-first.
- **CAMASA** (arXiv 2606.10641, VTC2026-Fall, June 2026) — real-world V2X *message* logs
  (40M+ CAMs, 2M+ DENMs) from Modena's MASA Living Lab, reconstructed into 14,000+ km of
  trajectories at 10Hz. Not sensor/LiDAR-based like OPV2V/V2X-Seq — built from actual
  deployed V2X message traffic, uniquely suited to studying *real* (not simulated) message
  loss/latency/penetration-rate effects.
- Not a fit: **Griffin** (arXiv 2503.06983) is aerial-ground cooperative detection/tracking,
  no clear trajectory-prediction benchmark component.
- No definitive "next V2X-Seq" in scale/standardization emerged — V2XPnP-Seq and
  UrbanIng-V2X are the closest candidates (both 2025, both real-world), neither yet a
  dominant leaderboard the way V2X-Seq/OPV2V currently are.

## Is the field still as underexplored as the survey found?

The survey's own count (Section VI-C): V2X-Seq and V2V4Real are each used by exactly one
paper in its corpus (refs [43] and [89] respectively — see the correction in
`REPO_ASSESSMENT.md`), a third cooperative dataset tracked by the review isn't used by any
surveyed paper at all. **Could not find a survey that re-quantified this exact statistic**,
so no hard updated number exists to cite. Qualitatively, unambiguous: the field visibly
picked up pace — roughly 8-10 dedicated cooperative-motion-forecasting papers in the last
12-18 months (listed above), two new dedicated datasets, and new dedicated workshop
infrastructure (CVPR 2026 "MEIS" workshop on cooperative/multi-agent intelligence, the 4th
DriveX workshop on foundation models for V2X cooperative driving — workshops are a leading
indicator a community is consolidating).

Evidence it's *not* yet crowded: a broad Sept 2025 cooperative-*perception* survey (arXiv
2509.24927) explicitly scopes itself to detection only, stating detection is cooperative
perception's "most representative task" — prediction isn't even mentioned as a subtopic.
Most new prediction papers also converge on the same two benchmarks (V2X-Seq, OPV2V/V2V4Real)
with incremental architectural tweaks — leaderboard-chasing on a couple of benchmarks, not
broad-based competition yet.

**Net read**: went from "virtually unclaimed" to "an active but still small, still-
consolidating niche" in about a year. The risk isn't "someone already published your exact
idea" — several papers are now competing on the same V2X-Seq leaderboard with incremental
fusion tweaks, so "yet another fusion architecture beating minADE by 2%" is a weaker bet
than a year ago. A paper opening a genuinely different axis (input representation/
robustness framing, a different collaboration mode, real-message-log data) still looks
well-positioned.

## Confidence / latency / occlusion as explicit prediction-stage input features

Searched specifically and repeatedly for this — the core premise of
`FIRST_EXPERIMENT_PROPOSAL.md`. **Nobody found does exactly this.** Closest partial
precedents, none matching fully:

- **MSMA** (arXiv 2407.21310, same authors as V2INet/`V2I_trajectory_prediction`) tests
  robustness under *synthesized* sensor noise and communication latency in CARLA — but as
  an evaluation condition/data augmentation, not as an explicit feature the model
  conditions on. Closest prior art in spirit.
- **CAMNet** builds its input representation from standardized V2V message fields but
  doesn't appear to model message loss/latency/reliability as features — CAMs treated as
  clean, ground-truth-like inputs.
- Delay-handling in cooperative *perception* fusion (V2X-ViT's delay-aware positional
  encoding, V2VNet's delay-compensation module, CMP's fixed 100ms synchronized window,
  V2X-Graph's interpolation-based sync) all handle latency implicitly, baked into the
  fusion architecture as compensation — not exposed as an interpretable, explicit
  per-agent feature at the prediction-input level.
- **CooperTrim** (arXiv 2602.13287, ICLR 2026) and **UECP** (arXiv 2606.23046, June 2026)
  do uncertainty/confidence-weighted feature selection — but at the *perception* stage
  (bandwidth-efficient sharing), confidence used internally for weighting, not exposed as
  an explicit input vector.
- **Reason-to-Transmit** (arXiv 2603.20308, Mar 2026) reasons about bandwidth/information-
  gain per region for perception-stage communication policy — perception-side, not
  prediction-input design.
- **V2X-RECT** treats noisy cross-view tracking association as something to filter/correct
  before prediction — conceptually adjacent but framed as error-correction, not as a
  feature the predictor is conditioned on.

**Confidence in this negative result**: moderate-high, not certain — a negative web search
doesn't rule out an obscure workshop paper or non-English venue, and "explicit input
featurization" is a specific-enough framing that a differently-worded paper could satisfy
it without matching the search terms used. Worth a repeat search before actually
submitting anything built on this premise.
