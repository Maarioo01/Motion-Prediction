# Datasets: the two remaining gaps

Everything else these 10 repos need (Argoverse 1, Argoverse 2, nuScenes, Waymo
`tf_example`) is already on `/raid`. Two things are still missing, both gated behind an
account/license step that has to be done by a human once, then becomes a plain CLI
command after.

## Waymo Open Motion Dataset, `scenario` format

Needed by TrajFlow, SceneInformer, GameFormer. `/raid/waymo` currently only has the
`tf_example` format — this is a genuinely separate download, not a conversion.

**One-time human step** (I can't do this part — it needs your own Google identity):

1. Go to **https://waymo.com/open/licensing/**, sign in with any Google account, and
   accept the Waymo Dataset License Agreement (non-commercial use). Any personal Gmail
   account works, no institutional email required.
2. `gcloud`/`gsutil` are already installed on this machine (Google Cloud SDK 583.0.0,
   at `~/google-cloud-sdk-installer/`, on `PATH` in new shells via `~/.bashrc`).
   Authenticate with that same account:
   ```bash
   gcloud auth login
   ```

**Then, download** (I've verified the bucket path structure and that `gsutil` needs
step 1+2 done first — anonymous access returns `401`):

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
larger, separate Perception dataset), so it should be well under your 2.7TB free, but
`gsutil du -sh` above will tell you exactly before you commit to the full pull.

Once downloaded, update `docker-compose.yml`'s volume mounts for `trajflow`,
`sceneinformer`, and `gameformer` to also mount `/raid/waymo/scenario` (they currently
only mount `/raid/waymo` for the `tf_example` data), then follow each repo's own data
preprocessing step (`TrajFlow`: `trajflow/datasets/waymo/data_preprocess.py`;
`SceneInformer`: `process_dataset.sh`; `GameFormer`: `interaction_prediction/data_process.py`).

## OPV2V + V2V4Real

Needed by CMP — and directly relevant to the V2X research direction (see
[`PHD_ROADMAP.md`](PHD_ROADMAP.md)). Unlike Waymo, **neither needs an account or
license click-through** — both are hosted on UCLA Box/Google Drive with no gate. The
practical friction is that Box/Drive aren't built for scripted bulk downloads the way
Waymo's GCS bucket is.

- **OPV2V**: https://opencood.readthedocs.io/en/latest/md_files/data_intro.html —
  UCLA Box (`https://ucla.app.box.com/v/UCLA-MobilityLab-OPV2V`) or Google Drive
  (`https://drive.google.com/drive/folders/1dkDeHlwOVbmgXcDazZvO6TFEZ6V_7WUu`).
  `train/validate/test/test_culvercity` splits, ~249GB total. Some splits are
  multi-part zips needing `cat train.zip.parta* > train.zip` before unzipping. Don't
  confuse the dataset Drive folder above with the separate one on UCLA's page that's
  just pretrained checkpoints (id `19aQPR50NyaqD2UlbFONwzMJXvANdLl55`).
- **V2V4Real**: https://mobility-lab.seas.ucla.edu/v2v4real/ — per-split UCLA Box
  links (train1–train8, test1–test3) listed directly on that page under hub
  `https://ucla.app.box.com/v/UCLA-MobilityLab-V2V4REAL`. CC BY 4.0 licensed. Get the
  OPV2V-format LiDAR+Labels version (matches what CMP's OpenCOOD-based pipeline
  expects), not the separate KITTI-format one. Size isn't published; per-frame density
  is comparable to OPV2V's.

Both were handed to a background download agent targeting `/raid/datasets/OPV2V` and
`/raid/datasets/V2V4Real` — check whether that completed before assuming you need to do
this by hand; if it's there, this section is just for reference/re-running later.

## After downloading

CMP's `docker-compose.yml` service currently has no dataset volume mount at all (none
were available at build time) — once OPV2V/V2V4Real land, add:

```yaml
  cmp:
    volumes:
      - ./repos/CMP:/workspace
      - /raid/datasets/OPV2V:/data/opv2v:ro
      - /raid/datasets/V2V4Real:/data/v2v4real:ro
```
