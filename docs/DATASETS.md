# Datasets

All datasets these 10 repos need are on `/raid`: Argoverse 1, Argoverse 2, nuScenes,
Waymo `tf_example`, Waymo `scenario`, OPV2V, and V2V4Real. No account-gated downloads
remain. What's left per-repo is each one's own *preprocessing* step (raw data → the
format that repo's dataloader actually expects), which is real work in its own right —
see [`TRAINING_PLAN.md`](TRAINING_PLAN.md).

## OPV2V + V2V4Real

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

Needed by TrajFlow, SceneInformer, GameFormer — distinct from the `tf_example` format
also on `/raid` (flattened tensors; `scenario` is protobuf `Scenario` messages, a
separate download from the same WOMD release, not a conversion of what's already
there). **Fully downloaded** at `/raid/waymo/scenario` (222GB), all 5 splits confirmed
complete: `training_20s` (1000 shards), `validation` (150), `testing` (150),
`validation_interactive` (150), `testing_interactive` (150).

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
