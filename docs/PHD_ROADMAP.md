# PhD roadmap — ideas, not a plan

> **Superseded on 2026-11-09.** The current plan is
> [`v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md`](v2x_plan/INFORME_PLAN_DE_RUTA_V2X.md) (section 12)
> and the first-paper summary [`v2x_plan/PAPER1_V2X_BENCHMARK.md`](v2x_plan/PAPER1_V2X_BENCHMARK.md).
> Two decisions there override this file: the thesis is 100 % V2X motion prediction, and
> **only real datasets** are used (OPV2V and other simulated data are dropped, so the
> "start in simulation" idea below no longer applies). Kept for history.

Written at the end of year 1, with the survey and this benchmark bench as the only two
concrete assets so far. This is deliberately loose — a set of directions to workshop
with your advisor, not a committed schedule. Revisit and rewrite this file as things
firm up; it should look wrong in six months if it's doing its job.

## Where things stand

- **Done**: a data-driven survey of the field (`SURVEY_itss.pdf`), and a working
  10-repo benchmark bench spanning the field's dominant architecture families
  (Transformer encoders, a flow-matching model, a GNN-pretraining variant, a
  cooperative pipeline) plus a full perception+planning stack for reference.
- **Stated end goal**: get to V2X motion forecasting by the end of the thesis, with
  real data, simulation, or both.

## Year 1 (remainder)

The gap between "survey done" and "first result" is usually the hardest part to
self-motivate through. Concrete, boring, low-risk things that build real competence:

1. **Reproduce one published number.** Pick QCNet (rank 1, cleanest codebase) or
   UniTraj's bundled MTR/Wayformer, train on Argoverse 2, and get within a reasonable
   margin of the paper's reported minADE/minFDE. This is not research — it's proof the
   bench, the data, and your own workflow are all actually correct, and it's the
   foundation every later comparison stands on.
2. **Pick one fast, cheap, survey-grounded empirical study as a first small paper /
   workshop submission**, rather than jumping straight to the big V2X contribution.
   Two candidates directly out of the survey's own Section VI, both runnable on data
   already on disk, no new dataset needed:
   - **Calibration/regret gap (VI.A)**: implement a calibration metric (or the Regret
     metric from [60]) on top of an existing baseline here and report how model
     rankings shift versus the standard minADE/minFDE leaderboard order. Directly
     extends a gap the survey already documents as unaddressed in its own corpus.
   - **Generalization gap (VI.D)**: perturb Argoverse2/Waymo map topology the way [4]
     did and measure how much QCNet/emp/RealMotion degrade. Cheap (no new data
     collection), and gives you an early, concrete sense of how brittle these
     "SOTA" numbers actually are before you build anything on top of them.
3. **Read CMP and V2I_trajectory_prediction's actual architectures properly** (not
   just get them building, which is done) — they're the only two V2X-relevant repos in
   the bench, and understanding exactly how they fuse cooperative information is the
   natural bridge into year 2.

## Year 1→2 transition: first V2X steps

Ideas, ordered roughly cheapest-to-hardest, not a sequence you need to follow in order:

- **Start in simulation, not real data.** OPV2V is already the easiest cooperative
  dataset to get (no account gate — see `DATASETS.md`) and is what CMP already expects.
  Getting *a* baseline V2X pipeline running end-to-end (even just reproducing CMP's own
  numbers) is a smaller lift than either collecting real data or designing a novel
  fusion module from scratch.
- **The narrowest possible V2X contribution**: instead of building a new
  three-stage pipeline like CMP's, try bolting cooperative information onto an
  *existing single-agent* backbone already in the bench (QCNet or a UniTraj backbone) —
  e.g. feed a second vehicle's shared trajectory prediction in as extra "surrounding
  agent" context tokens, reusing the encoder's existing agent-interaction machinery
  rather than inventing a new fusion architecture. Small, testable, directly measures
  whether cooperative *predictions* (not raw sensor fusion) help — a genuinely open
  question given how thin the survey's own cooperative-signals coverage is (Section
  VI.C: only 2 of ~106 corpus papers use a cooperative dataset at all).
- **Physics/kinematic angle**: the survey's Section V.A physics-and-rule-based family
  (Kalman/UKF fusion of learned + kinematic predictions, e.g. [13]'s UKF-based
  right-of-way resolution) is a smaller, more classical sub-area that composes
  naturally with V2X — a Kalman filter is a natural way to fuse a noisy cooperative
  signal (another vehicle's shared, possibly-latency-affected prediction) with your own
  vehicle's locally-computed one, and it's a well-understood tool rather than a novel
  architecture, which lowers implementation risk while you're still building V2X
  intuition.
- **Communication-efficiency framing**: CMP's own motivation (and the wider
  cooperative-perception literature it doesn't cite, e.g. Where2comm-style
  bandwidth-aware fusion) treats "what to share, not just how to fuse it" as a first-
  class question. Worth reading into before committing to an architecture, since it
  reframes the problem from "add more information" to "add the *right* information
  under a bandwidth budget" — a more defensible thesis angle than "cooperative beats
  non-cooperative," which is a fairly low bar.

## Year 2: real data, if it's time

- **Validate the simulation-derived findings against real data.** If the year-1/2
  simulated-V2X module showed a benefit on OPV2V, the natural year-2 question is
  whether it holds on V2V4Real (real-world V2V) — a sim-to-real generalization angle
  that's a paper in itself even independent of the core method.
- **Scale the fusion module across more of the bench's backbones** once the core idea
  is validated on one — this is where UniTraj's multi-backbone harness pays for itself:
  the same cooperative-context module tested against AutoBot, MTR, and Wayformer
  simultaneously is a much stronger empirical claim than one backbone alone.

## Year 3: consolidation

- Thesis-scale ablations across simulated + real V2X data, whichever backbone(s) the
  year 2 work converged on.
- Revisit the interpretability gap (Section VI.E) as a secondary contribution if time
  allows — a V2X model is a natural place for it, since "why did the fused prediction
  change" is a more concrete, answerable question than for a single-agent model.
- Writing, defense prep, and (if the AGPLv3 UniTraj dependency is still load-bearing by
  then) confirm with your institution what that means for the thesis code release.

## A note on pacing

This document front-loads a lot of "cheap, low-risk" ideas for year 1→2 deliberately —
the biggest risk after a strong survey year is spending another 6+ months on
infrastructure/tooling with nothing empirical to show. The bench built this session
removes most of that excuse; the next concrete step is picking *one* item from "Year 1
(remainder)" above and actually running it, not adding more repos or datasets.
