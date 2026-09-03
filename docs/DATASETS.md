# Datasets

Status as of the datasets actually landing: Argoverse 1, Argoverse 2, nuScenes, Waymo
`tf_example`, OPV2V, and V2V4Real are all on `/raid`. Waymo's `scenario` format is the
one gap left, gated behind an account/license step only you can do.

## OPV2V + V2V4Real — done, already mounted

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

## Waymo Open Motion Dataset, `scenario` format — the one remaining gap

Needed by TrajFlow, SceneInformer, GameFormer. `/raid/waymo` currently only has the
`tf_example` format — this is a genuinely separate download, not a conversion.

**One-time human step** (can't be done unattended — it needs your own Google identity):

1. Go to **https://waymo.com/open/licensing/**, sign in with any Google account, and
   accept the Waymo Dataset License Agreement (non-commercial use). Any personal Gmail
   account works, no institutional email required.
2. `gcloud`/`gsutil` are already installed on this machine (Google Cloud SDK 583.0.0,
   at `~/google-cloud-sdk-installer/`, on `PATH` in new shells via `~/.bashrc`).
   Authenticate with that same account:
   ```bash
   gcloud auth login
   ```

**Then, download** (bucket path structure verified; anonymous access returns `401`
without steps 1+2 first):

```bash
# Cheap first: see what's actually there before committing to a full pull
gsutil ls gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/
gsutil du -sh gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/

# One shard, to sanity-check before pulling everything
gsutil cp gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/validation/validation.tfrecord-00000-of-00150 /raid/waymo/scenario_test/

# Full scenario-format release
mkdir -p /raid/waymo/scenario
gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/training_20s /raid/waymo/scenario/
gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/validation /raid/waymo/scenario/
gsutil -m cp -r gs://waymo_open_dataset_motion_v_1_3_0/uncompressed/scenario/testing /raid/waymo/scenario/
# Also check for validation_interactive/ and testing_interactive/ once `gsutil ls`
# above shows you the live listing - GameFormer's README specifically calls these out.
```

Waymo doesn't publish an official size figure for the scenario release. It's protobuf
trajectories + map + traffic-light state only (not raw sensor data — that's the much
larger, separate Perception dataset), so it should fit comfortably in whatever's free
on `/raid`, but `gsutil du -sh` above will tell you exactly before committing to the
full pull.

Once downloaded, update `docker-compose.yml`'s volume mounts for `trajflow`,
`sceneinformer`, and `gameformer` to also mount `/raid/waymo/scenario` (they currently
only mount `/raid/waymo` for the `tf_example` data), then follow each repo's own data
preprocessing step (`TrajFlow`: `trajflow/datasets/waymo/data_preprocess.py`;
`SceneInformer`: `process_dataset.sh`; `GameFormer`: `interaction_prediction/data_process.py`).
