# Datasets

Real datasets only (CLAUDE.md, standing decision 1). What is on `/raid` as of 2026-11-11:

| Path | Size | Used by |
| --- | --- | --- |
| `/raid/datasets/V2X-Seq-TFD/V2X-Seq-TFD` | 125 GB (+63 GB zips in `_zips/`) | V2X baselines (V2X-Graph, HiVT plugin, V2INet, Co-MTP) |
| `/raid/datasets/V2X-Traj/v2x-traj` | 11 GB | V2X-Graph |
| `/raid/datasets/V2V4Real` | 41 GB | CMP |
| `/raid/argoverse2` | — | QCNet (pretraining / checkpoint sanity check) |
| `/raid/argoverse1_1` | 327 GB | kept until the HiVT sanity check (official HiVT checkpoints are AV1); then delete |
| `/raid/waymo/scenario` (`training`, `validation`, `testing`, `*_interactive`) | — | kept (Mario's choice), no active service |
| `/raid/nuscenes` | — | GaussianCaR collaboration |
| `/raid/scratch/qcnet_data_staging` | — | QCNet preprocessing caches |

**Deleted on 2026-11-11 (checklist A3, approved by Mario):** `/raid/datasets/OPV2V`
(197 GB, simulated), `/raid/waymo/scenario/training_20s` (87 GB, only SceneInformer),
`/raid/scratch/{gameformer,trajflow,mtr,sceneinformer}_data_staging` (1.3 TB + 592 GB +
491 GB + 205 GB, archived repos' preprocessing), `repos/pretraining-synthetic` (bundled
synthetic set), and the archived Docker images (`mtr`, `realmotion`, `sceneinformer`,
`gameformer`). The sections below on OPV2V and the Waymo staging are kept as history.

**Waymo `tf_example` was deleted** (was ~1.1TB, at `/raid/waymo/tf_example`) — it was
never used by any of the 11 built repos, all of which need `scenario` format
specifically (see below). Deleted deliberately to relieve real disk pressure while
GameFormer/TrajFlow/MTR's full-scale preprocessing was running. If ever needed again,
it's re-downloadable via the same `gcloud`/`gsutil` flow as `scenario` (just a
different bucket subpath), not something this project has any use for otherwise.

## V2X-Seq-TFD and V2X-Traj (Phase 0, A1/A2)

Both come from public Google Drive links in the official AIR-THU repos; no login, form or
click-through. The "free download only in mainland China" note in `AIR-THU/DAIR-V2X-Seq`
is outdated: the full train + val set is in the public Drive folder linked from
`AIR-THU/DAIR-V2X` ("Public-V2X-Datasets") and from the `AIR-THU/V2X-Graph` README. The
test splits are not released, so published numbers (V2X-Graph etc.) are on val. The
dataset terms of use are on <https://thudair.baai.ac.cn/index> (the code repos are Apache-2.0).

- **V2X-Traj** — `/raid/datasets/V2X-Traj/v2x-traj` (11 GB unzipped; zip kept in
  `_zips/`). Drive file `1-5cPcZfGx1L58aiNiHUGoJOkoTSojFtF` (`v2x-traj.zip`, 2.6 GB).
  `ego-`, `vehicle-`, `infrastructure-trajectories/{train,val}` with 6062 train / 2020 val
  scenarios each, plus `traffic-light/`, `maps/`, `map_files/` (Argoverse-1-style
  Yizhuang map tables). Downloaded 2026-11-10.
- **V2X-Seq-TFD** — `/raid/datasets/V2X-Seq-TFD/V2X-Seq-TFD` (125 GB, 309,636 files;
  split parts + joined zip kept in `_zips/`, 63 GB). Downloaded 2026-11-11 from Mario's
  own Drive copy via the browser, because the public files stayed quota-blocked for over
  a day. Joined zip passes `unzip -t`. Scenarios per split: cooperative view 25,574 train /
  10,229 val (each with `cooperative-`, `vehicle-`, `infrastructure-trajectories` and
  `traffic-light`); `single-infrastructure` 39,427 / 15,770; `single-vehicle` 40,001 /
  16,000; 28 maps (`maps/yizhuang_hdmap*.json`). Cooperative CSVs carry extra columns
  `vic_tag`, `from_side`, `car_side_id`, `road_side_id`. Source: Drive folder
  `1yDnlrPCKImpVfI1OPBYyzLFWkhZP5v-7`, `Full Dataset (train & val)/`: split zip
  `V2X-Seq-TFD.z01`–`.z06` (5.0 GB each) + `V2X-Seq-TFD.zip` (1.3 GB), ~31 GB in total.
  Join with `zip -s 0 V2X-Seq-TFD.zip --out full.zip` (or `7z x V2X-Seq-TFD.zip`) before
  extracting. Expected layout: `cooperative-vehicle-infrastructure/{cooperative,vehicle,
  infrastructure}-trajectories`, `traffic-light`, `maps/` — see
  `AIR-THU/DAIR-V2X-Seq/dataset/v2x-seq-tfd/README.md`. Anonymous download is often
  blocked by Drive's per-file quota ("Too many users have viewed or downloaded this file
  recently"); retry later, or add the folder to your own Drive and download from there.

## OPV2V + V2V4Real (OPV2V deleted 2026-11-11; history)

Needed by CMP, and directly relevant to the V2X research direction (see
[`PHD_ROADMAP.md`](PHD_ROADMAP.md)). **Both are fully downloaded and extracted**, at
`/raid/datasets/OPV2V` (197GB: `train/`, `validate/`, `test/`, `test_culvercity/`) and
`/raid/datasets/V2V4Real` (41GB: `train/`, `validate/`, `test/`) — confirmed via the
download pipeline's own exit codes (`opv2v_rc=0 v2v4real_rc=0`) and a manual check of
each folder. `docker-compose.yml`'s `cmp` service already mounts both, read-only, at
`/data/opv2v` and `/data/v2v4real`.

Neither needed an account or license click-through — both are hosted on UCLA
Box/Google Drive with no gate, unlike Waymo below. The only real friction was that
Box/Drive aren't built for scripted bulk downloads the way a GCS bucket is: a
background agent had to reverse-engineer Box's shared-folder direct-download URL
pattern (`https://ucla.app.box.com/index.php?rm=box_download_shared_file&shared_name=...&file_id=...`)
since the page links you'd click by hand aren't themselves downloadable via `curl`/`wget`.

**If you ever need to redo this** (a corrupted split, a fresh machine, etc.), the
official sources are:

- **OPV2V**: https://opencood.readthedocs.io/en/latest/md_files/data_intro.html —
  UCLA Box (`https://ucla.app.box.com/v/UCLA-MobilityLab-OPV2V`) or Google Drive
  (`https://drive.google.com/drive/folders/1dkDeHlwOVbmgXcDazZvO6TFEZ6V_7WUu`). Don't
  confuse that Drive folder with the separate one on UCLA's page that's just
  pretrained checkpoints (id `19aQPR50NyaqD2UlbFONwzMJXvANdLl55`).
- **V2V4Real**: https://mobility-lab.seas.ucla.edu/v2v4real/ — per-split UCLA Box
  links (train1–train8, test1–test3) listed directly on that page under hub
  `https://ucla.app.box.com/v/UCLA-MobilityLab-V2V4REAL`. CC BY 4.0 licensed. The
  OPV2V-format LiDAR+Labels version is what's downloaded here (matches what CMP's
  OpenCOOD-based pipeline expects), not the separate KITTI-format one.

## Waymo Open Motion Dataset, `scenario` format

*2026-11-11: `training_20s` deleted (A3); the other splits stay. The services below are archived.*

Needed by TrajFlow, SceneInformer, GameFormer, and MTR (added later, see
`MODELS_OVERVIEW.md`) — distinct from the `tf_example` format
also on `/raid` (flattened tensors; `scenario` is protobuf `Scenario` messages, a
separate download from the same WOMD release, not a conversion of what's already
there). At `/raid/waymo/scenario` (647GB), 6 splits confirmed complete: `training`
(1000 shards, 425GB), `training_20s` (1000 shards), `validation` (150), `testing`
(150), `validation_interactive` (150), `testing_interactive` (150).

**`training_20s` is not a drop-in replacement for the plain `training` split** — they're
different scenario populations, not just different clip lengths. Confirmed by directly
parsing scenarios from each: `training_20s` has `tracks_to_predict` **always empty**,
while plain `training`/`validation`/`testing` have it populated (3-7 entries/scenario).
SceneInformer's occlusion pipeline doesn't care (it doesn't use `tracks_to_predict`),
which is why `training_20s` was downloaded in the first place — but GameFormer's
`interaction_prediction/data_process.py` and TrajFlow's
`trajflow/datasets/waymo/data_preprocess.py` both key off `tracks_to_predict`, so both
need the plain split for a real training run (see `BUILD_GOTCHAS.md`); MTR's own
`mtr/datasets/waymo/data_preprocess.py` (what TrajFlow's was derived from) needs it
too. **The plain `training` split is now downloaded** (1000 shards, 425GB) —
GameFormer and TrajFlow can both now run full-scale preprocessing, not just the
small-subset verification done
against `validation` earlier (see `TRAINING_PLAN.md`).

No `docker-compose.yml` changes were needed — `trajflow`, `sceneinformer`, and
`gameformer` already mount the whole `/raid/waymo` directory (not just `tf_example`),
so `scenario/` appears at `/data/waymo/scenario` inside each container automatically
(verified).

**What's still needed is each repo's own preprocessing** — raw `scenario` tfrecords
aren't directly trainable, each repo has its own pipeline converting them into its own
format:

- **SceneInformer**: a 4-stage pipeline (`scripts/collect_raw_meas.py` →
  `scripts/generate_occlusion_dataset.py` [the slow step] →
  `scripts/generate_dataset_summary.py` → `scripts/index_dataset.py`), **verified
  working end-to-end** on a small staged subset this session (see
  [`TRAINING_PLAN.md`](TRAINING_PLAN.md) for the exact commands and two real upstream
  bugs that had to be patched first). Not yet run at full scale (1000/150 shards).
- **TrajFlow**: `trajflow/datasets/waymo/data_preprocess.py` — not yet attempted.
- **GameFormer**: `interaction_prediction/data_process.py` — not yet attempted.

**If you ever need to redo the raw download** (a fresh machine, a corrupted shard,
etc.), it needs your own Google account — this part can't be done unattended:

1. Go to **https://waymo.com/open/licensing/**, sign in with any Google account, and
   accept the Waymo Dataset License Agreement (non-commercial use). Any personal Gmail
   account works, no institutional email required.
2. `gcloud`/`gsutil` are already installed on this machine (Google Cloud SDK 583.0.0,
   at `~/google-cloud-sdk-installer/`, on `PATH` in new shells via `~/.bashrc`).
   Authenticate with that same account:
   ```bash
   gcloud auth login
   ```
3. Download (bucket path structure verified; anonymous access returns `401` without
   steps 1+2 first):
   ```bash
   gsutil ls gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/
   mkdir -p /raid/waymo/scenario
   gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/training_20s /raid/waymo/scenario/
   gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/validation /raid/waymo/scenario/
   gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/testing /raid/waymo/scenario/
   gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/validation_interactive /raid/waymo/scenario/
   gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/testing_interactive /raid/waymo/scenario/
   ```
