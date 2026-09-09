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

## Note on the second presentation (task 4)

You asked for a second, more elaborate presentation specifically about the first-paper
idea (`FIRST_EXPERIMENT_PROPOSAL.md`'s CMP aggregation-module proposal). That's a
separate deliverable from this one — worth its own project or at least its own kickoff
prompt, since the audience and purpose are different (pitching a specific research
contribution vs. surveying the whole benchmark). Come back to this doc once the first
presentation's structure is settled; the same "upload knowledge, paste instructions,
kickoff with an outline request first" pattern applies, just pointed at
`FIRST_EXPERIMENT_PROPOSAL.md` and `RECENT_V2X_LITERATURE.md` as the primary sources
instead.
