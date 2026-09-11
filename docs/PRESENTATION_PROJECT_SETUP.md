# Setting up the presentation work in a Claude web Project

This doc is the handoff package for the "build a sophisticated presentation" work you
want to do in a separate Claude.ai session — everything needed to set that session up
lives here, so nothing has to be re-explained from scratch over there. This covers the
**first** presentation (datasets + models + architectures landscape). The **second**
one (the first-paper pitch) is a separate task — see the note at the bottom.

## Steps on claude.ai

1. Go to claude.ai → **Projects** → **Create project**.
2. Name it something like **"Motion Prediction — Benchmark Overview"**.
3. Open **Project knowledge** and upload these files from this repo (exact paths below).
4. Paste the **Project instructions** block below into the project's custom instructions.
5. Start a new chat inside the project and paste the **kickoff prompt** below as your
   first message.

## Files to upload as Project knowledge

From `/home/baco/dockers/MOTION_PREDICTION/`:

- `docs/MODELS_OVERVIEW.md` — the core reference: architecture/datasets/metrics/results/
  license/limitations for all 13 repos considered (11 built), pulled from the papers
  themselves, plus the dataset-usage and model-similarity figures.
- `docs/figures/dataset_usage_matrix.png`, `docs/figures/model_similarity_matrix.png`,
  `docs/figures/av2_head_to_head.png` — already-generated comparison figures, reusable
  directly or as a starting point for restyled versions.
- `docs/DATASETS.md` — exact dataset status, sizes, splits, formats for everything
  actually in use (Argoverse 1/2, WOMD `scenario`+`tf_example`, nuScenes, OPV2V,
  V2V4Real).
- `docs/REPO_ASSESSMENT.md` — the "why these models" reasoning, tiered by purpose.
- `docs/TRAINING_PLAN.md` and `docs/BUILD_GOTCHAS.md` — per-repo preprocessing pipelines
  and the real reasons each one works the way it does (shared code lineage between
  MTR/TrajFlow, why GameFormer's preprocessing produces pairs not whole scenarios, why
  SceneInformer is a 4-stage pipeline, etc.).
- `docs/RECENT_V2X_LITERATURE.md` — the newer V2X datasets/papers (V2XPnP-Seq,
  UrbanIng-V2X, CAMASA, etc.) that aren't yet reflected in `DATASETS.md` since they
  aren't downloaded, but matter for a "landscape" slide.
- `docs/SURVEY_itss.pdf` — your own survey paper, for the taxonomy/gap-analysis slides.
- `docs/PHD_ROADMAP.md` — for framing why this set of models/datasets, in the context of
  the 2-3 year plan.

## Project instructions (paste as-is into the project's custom instructions)

```
You're helping build a polished, visually-designed presentation summarizing a PhD
motion-forecasting benchmark project (11 Docker-ized model repos + their datasets,
built as infrastructure for a PhD in motion forecasting for autonomous driving, with an
eventual V2X/cooperative-perception thesis direction). The audience is the student
themselves plus their advisor/committee — treat this as a real academic presentation,
not marketing collateral.

Ground every factual claim (architecture details, dataset sizes, metrics, results) in
the uploaded project knowledge files, not general knowledge or assumption — this project
already did the work of verifying these facts against the original papers, so trust the
uploaded docs over anything you'd otherwise recall about these models. If something
isn't covered in the knowledge files, say so explicitly rather than filling the gap with
a plausible-sounding guess.

Build this as an Artifact-based slide deck (use the design/canvas tooling available to
you). Prioritize clarity and information density appropriate for a technical audience
over decoration - real comparison tables, real numbers, real architecture structure, not
generic stock-photo-style AI slides. When describing a model's architecture, prefer a
clean original diagram over reproducing a paper's own figure directly (consistent visual
style across slides matters more than matching each paper's own aesthetic, and avoids
any reproduction concerns) - only fall back to describing a paper's figure in words if a
diagram isn't feasible.

Work iteratively: propose a slide-by-slide outline first and confirm it before building
the full deck, since this is a big, multi-part presentation and getting the structure
wrong costs more time than getting the styling wrong.
```

## Kickoff prompt (first message in the new chat)

```
I want a sophisticated, visually rich presentation covering my PhD motion-forecasting
benchmark project. Structure it around these sections - pull the actual content from
the uploaded knowledge files, don't summarize from general knowledge:

1. Datasets landscape: every dataset actually in use (Argoverse 1, Argoverse 2, WOMD
   scenario + tf_example formats, nuScenes, OPV2V, V2V4Real), each with its specific
   features - size, sensors/annotations, splits, sampling rate, prediction horizon,
   license. Then a second slide (or set) for datasets that exist in the wider field but
   aren't in use yet (V2XPnP-Seq, UrbanIng-V2X, CAMASA), framed as "landscape context /
   possible future data."

2. The models chosen: all 11 repos, each with its crucial design decision and why it
   matters (e.g. QCNet's query-centric caching, MTR's fixed intention-point anchors,
   CMP's Prediction Aggregation Module, TrajFlow's flow-matching, UniTraj as a framework
   rather than a model). Group them the way REPO_ASSESSMENT.md does (tiers by purpose),
   not just an alphabetical list.

3. Shared vs. distinct features across models: use the dataset-usage matrix and
   model-similarity matrix figures already generated (or rebuild them in this deck's
   visual style) to show which models share benchmarks/approaches and which are
   standalone.

4. Preprocessing, model by model: what raw data becomes what training format for each
   repo, and *why* each one made that choice (e.g. why GameFormer's preprocessing
   produces ego-neighbor pairs rather than whole-scenario tensors, why TrajFlow's
   preprocessing script is literally derived from MTR's, why SceneInformer needs a
   4-stage pipeline for occlusion inference). This is where the "why each one decided to
   do it this way" question gets answered concretely, not just described.

5. Architecture deep-dives: for the most important models (at minimum QCNet, MTR, CMP,
   TrajFlow, UniTraj), a dedicated slide with a clean diagram of the actual architecture
   - encoder/decoder structure, key mechanism (query pairs, flow matching, aggregation
   module, etc.), not just a paragraph of prose.

Start with a proposed slide-by-slide outline before building anything, so I can adjust
the structure first.
```

## Second presentation: the first-paper pitch (task 4)

A separate, more elaborate deck specifically pitching the CMP aggregation-module
proposal (`FIRST_EXPERIMENT_PROPOSAL.md`) as the first real research contribution —
different audience/purpose from the benchmark-overview deck above (arguing for a
specific idea, not surveying everything), so it gets its own project rather than being
folded into the first one. Same overall pattern: create a project, upload knowledge,
paste instructions, kick off with an outline request.

### Steps on claude.ai

1. **Projects → Create project**, name it **"Motion Prediction — First Paper Pitch"**.
2. Upload the knowledge files listed below.
3. Paste the **Project instructions** block into custom instructions.
4. New chat, paste the **kickoff prompt** as the first message.

### Files to upload as Project knowledge

- `docs/FIRST_EXPERIMENT_PROPOSAL.md` — the core proposal: motivation, the two ablation
  arms, evaluation plan, risks, scope.
- `docs/CMP_MTR_CODE_EXCERPTS.md` — the actual code snippets behind the proposal (the
  disabled decoder, the naive slice, MTR's core mechanism) — needed for an *accurate*
  architecture diagram, since the other session won't have filesystem access to the
  actual cloned repos.
- `docs/RECENT_V2X_LITERATURE.md` — situates the idea against current work, especially
  the April 2026 late-fusion critique paper that argues against CMP's whole design
  philosophy.
- `docs/MODELS_OVERVIEW.md` — CMP's and MTR's full reference entries (results tables,
  license, limitations) for anyone wanting the fuller picture behind a given slide.
- `docs/PHD_ROADMAP.md` — for the closing "how this fits the 2-3 year plan" framing.
- `docs/figures/dataset_usage_matrix.png` and `model_similarity_matrix.png` — reusable
  if a slide wants to show where CMP/MTR sit relative to the rest of the bench.

### Project instructions (paste as-is)

```
You're helping build a detailed, persuasive presentation pitching a specific first
research contribution for a motion-forecasting PhD (V2X/cooperative-perception
direction). The audience is the student's advisor - this needs to read as a genuine
research pitch with a real technical finding behind it, not a status update or a
generic "here's an idea" slide.

The core finding: CMP (a cooperative-prediction pipeline already in the student's
benchmark) has a real, identifiable weakness in its Prediction Aggregation Module - a
permutation-invariant query-based decoder is written in the code but never used,
replaced by a naive order-dependent slice - and a literature search found nobody in the
current cooperative-prediction literature treats per-agent confidence, communication
latency, or occlusion as an explicit prediction-stage input feature. The proposal
combines fixing the first (a concrete, low-risk ablation) with the second (the more
novel contribution).

Ground every technical claim in the uploaded knowledge files - the code excerpts file
in particular has the exact mechanism this needs to accurately diagram (which module
does what, where the bug is, what the fix changes). Do not paraphrase the architecture
from memory or guess at what CMP/MTR do generically - use the actual snippets provided.

Build this as an Artifact-based deck. This one should go deeper than a typical overview
presentation: include a precise before/after diagram of the aggregation module (current
naive-slice flow vs. proposed permutation-invariant + confidence-weighted flow), an
honest slide on risks/counterarguments (especially the late-fusion critique paper - this
needs a real answer, not a dismissal), and a clear ablation table mockup showing exactly
what the three-row comparison (baseline / fixed-pooling / fixed-pooling+confidence) is
meant to demonstrate. Propose a slide outline first and confirm before building the full
deck.
```

### Kickoff prompt (first message in the new chat)

```
Build a presentation pitching my first PhD research contribution: improving CMP's
Prediction Aggregation Module for cooperative motion prediction. Pull all technical
content from the uploaded files, not general knowledge. Structure:

1. Framing: the V2X/cooperative-prediction thesis direction, and why this specific
   module (not a new architecture) is the right first target - low risk, builds
   directly on infrastructure already validated, still genuinely novel.

2. Background walkthrough: CMP's 3-stage pipeline (detection -> tracking -> per-CAV MTR
   prediction -> aggregation), with the aggregation stage highlighted as where this
   contribution lives. Include MTR's core mechanism (intention points + iterative
   refinement) since the aggregation module wraps it directly.

3. The finding: a precise diagram of MotionAggregatorTransformer's actual forward pass
   - self-attention over concatenated per-CAV-trajectory + BEV + map embeddings, then
   the disabled query-based decoder vs. the naive slice that's actually used. Make the
   "written but never called" detail visually obvious - this is the concrete evidence
   the whole pitch rests on.

4. The literature gap: nobody treats per-agent confidence/latency/occlusion as an
   explicit prediction-stage input feature (cite the specific papers checked and ruled
   out - MSMA, CAMNet, CooperTrim, UECP, V2X-RECT - and why each doesn't count).

5. The proposal: Arm A (fix the pooling - use the existing disabled decoder or a
   permutation-invariant alternative) and Arm B (confidence-weight each CAV's
   contribution), as two separable, ablatable changes - diagram the proposed modified
   flow directly next to the current one from slide 3.

6. Evaluation plan: the 3-row ablation table (baseline CMP / +Arm A / +Arm A+B) on
   OPV2V and V2V4Real, same metrics as CMP's own paper - mock up what this table will
   look like once results exist.

7. Anticipated pushback: the late-fusion critique paper directly challenges CMP-style
   fusion - give this its own slide with a real response, not a dismissal (e.g.
   confidence-aware early fusion as a direct comparison point against their late-fusion
   alternative).

8. Honest risks: per-box confidence might not be cleanly available without rerunning
   detection, the improvement might wash out once Arm A is isolated, scope is
   deliberately small.

9. Fit with the broader plan: where this sits in the 2-3 year roadmap if it works out,
   and what a negative result would still be worth.

Propose the slide outline first, then build once I confirm it.
```
