# Phase 0 checklist — "V2X ground floor" (Nov 2026 – Jan 2027)

Working tracker for Phase 0 of the plan in [`INFORME_PLAN_DE_RUTA_V2X.md`](INFORME_PLAN_DE_RUTA_V2X.md)
(section 12.1). Tick items here as they are done, with the date and a one-line note
(where the data lives, the commit, the number obtained). Keep the Spanish report as the
source of *why*; this file is the source of *what is done*.

**Gate to leave Phase 0:** two published V2X-Seq numbers reproduced within ±5 %
(HiVT and V2X-Graph with its checkpoint).

## A. Data (real datasets only)

- [x] **A1. V2X-Seq-TFD** (trajectory forecasting part of V2X-Seq, ~51k cooperative
      scenarios, 10 s at 10 Hz). Find the access route from Spain (official repo
      `AIR-THU/DAIR-V2X-Seq` says free download is for mainland China; look for the
      international application form / OpenDataLab / other official mirror). Download to
      `/raid/datasets/V2X-Seq-TFD`.
      *2026-11-10: access route found — public Drive folder linked from `AIR-THU/DAIR-V2X`
      and `AIR-THU/V2X-Graph` (train + val, ~31 GB split zip, no form). Download blocked
      for now by Drive's per-file quota; see `docs/DATASETS.md`.*
      *2026-11-11: done — via Mario's Drive copy. `/raid/datasets/V2X-Seq-TFD/V2X-Seq-TFD`,
      125 GB; cooperative view 25,574 train / 10,229 val, 28 maps; zip passes `unzip -t`.*
- [x] **A2. V2X-Traj** (~10k scenarios, 2 vehicles + infrastructure, 28 intersections).
      Linked from `AIR-THU/V2X-Graph` (Google Drive). Download to `/raid/datasets/V2X-Traj`.
      *2026-11-10: done — `/raid/datasets/V2X-Traj/v2x-traj`, 6062 train / 2020 val
      scenarios (test not released), zip passes `unzip -t`.*
- [x] **A3. Real-data-only cleanup**: OPV2V and any simulated/synthetic data removed from
      disk (see CLAUDE.md "Datasets" for the keep/delete list). `docs/DATASETS.md` updated.
      *2026-11-11: done — OPV2V, `training_20s`, 4 staging folders, pretraining-synthetic
      and 4 archived images deleted (~3.1 TB on `/raid`, 61 GB on `/`). AV1 kept until the
      HiVT sanity check.*

## B. Methods in the bench

- [x] **B1. Archive** the configs not needed for the V2X plan into `docker/_archive/`
      (out of `setup.sh` and `docker-compose.yml`). See CLAUDE.md "Methods".
      *2026-11-10: 9 configs moved with `git mv`; restore notes in
      `docker/_archive/README.md`. Active: qcnet, cmp (both pass `verify.sh`). CMP's OPV2V
      mount removed. Images, `repos/` clones and staging data untouched (A3).*
- [x] **B2. Add V2X-Graph** (`AIR-THU/V2X-Graph`, code + checkpoint) as a Docker service.
      *2026-11-12: service `v2x-graph` (Python 3.10, torch 1.12.1+cu116, GPU0), passes
      `verify.sh`; all 6 checkpoints fetched via LFS. Upstream commit `b6cf34b`,
      DAIR-V2X-Seq `8a5b4f8`, argoverse-api `f886ac5`. TFD layout/maps/labels/caches in
      `/raid/scratch/v2xgraph_data`. Build notes in `BUILD_GOTCHAS.md`.*
- [ ] **B3. Add V2INet** (`xichennn/V2I_trajectory_prediction`, already in `setup.sh --all`).
- [ ] **B4. Add Co-MTP** (`xiaomiaozhang/Co-MTP`, code only; note its 3 s → 5 s @ 5 Hz
      protocol and its use of the AV's ground-truth future as "plan" — privileged info).
- [ ] **B5. HiVT** baseline (`ZikangZhou/HiVT`) — check whether V2X-Seq's own baseline code
      already provides it before adding a separate service.
      *2026-11-10: it does — `AIR-THU/DAIR-V2X-Seq` `projects/HiVT_plugin` (PP-VIC eval
      scripts); no checkpoint in the repo.*

## C. Reproduction (the gate)

- [ ] **C1.** HiVT on V2X-Seq: number obtained vs published (V2X-Graph paper, Table 1:
      1.12 / 1.97 / 0.30 for HiVT + PP-VIC).
- [x] **C2.** V2X-Graph checkpoint on V2X-Seq: number obtained vs published (1.05 / 1.79 / 0.25).
      *2026-11-12: reproduced on TFD val — V2I 1.046 / 1.787 / 0.254, ego-only 1.160 /
      2.021 / 0.303 (published 1.16 / 2.02 / 0.30). Commit `b6cf34b` + one compatibility
      patch (PyG 2.x `__inc__` signature); details in [`docs/RESULTS.md`](../RESULTS.md).*
- [ ] **C3.** Record for every run: upstream commit hash, config, seed, split, number.
      *2026-11-12: ledger started in [`docs/RESULTS.md`](../RESULTS.md) (ongoing).*

## D. Warm-up and side tasks

- [ ] **D1. CMP on V2V4Real only**: validate the released checkpoint (Track A of
      `docs/TRAINING_PLAN.md`), then Arm A of
      [`FIRST_EXPERIMENT_PROPOSAL.md`](../FIRST_EXPERIMENT_PROPOSAL.md) (enable the
      query-based decoder instead of the `rows[:6]` slice). 1–2 weeks max.
- [ ] **D2.** Email to the GaussianCaR colleague proposing option B (report section 6.2),
      meeting to agree interface and authorship. Option C still to review (comment C3 in
      the report).
