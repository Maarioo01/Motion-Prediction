#!/bin/bash
# Builds the directory layout V2X-Graph's V2X-Seq-TFD code expects, as a writable tree of
# symlinks into the read-only dataset mount. Run inside the v2x-graph container:
#   bash prepare_tfd_layout.sh            (defaults below)
#
# Why: the released TFD has <view>/<split>/*.csv, while V2X-Graph reads
# <view>/<split>/data/*.csv; it also writes its outputs (merged maps, matching labels,
# .pt caches) next to the raw data, and it reads a 'v2x_fusion' folder that no released
# script creates. Upstream issue AIR-THU/V2X-Graph#6: 'v2x_fusion' is the vehicle-side
# trajectories, so it is linked to vehicle-trajectories here.
set -euo pipefail
SRC=${1:-/data/v2x-seq-tfd}                # read-only V2X-Seq-TFD root (has maps/, cooperative-vehicle-infrastructure/)
DST=${2:-/workspace/data_staging/tfd}      # writable; bind-mounted from /raid/scratch/v2xgraph_data

[ -d "$SRC/cooperative-vehicle-infrastructure" ] || { echo "no TFD at $SRC"; exit 1; }
COOP_SRC=$SRC/cooperative-vehicle-infrastructure
COOP_DST=$DST/cooperative-vehicle-infrastructure

mkdir -p "$DST" "$DST/map_files"
ln -sfn "$SRC/maps" "$DST/maps"

for split in train val; do
  for view in vehicle-trajectories infrastructure-trajectories cooperative-trajectories traffic-light; do
    mkdir -p "$COOP_DST/$view/$split"
    ln -sfn "$COOP_SRC/$view/$split" "$COOP_DST/$view/$split/data"
  done
  mkdir -p "$COOP_DST/v2x_fusion/$split" "$COOP_DST/traj_match_labels/$split/data"
  ln -sfn "$COOP_SRC/vehicle-trajectories/$split" "$COOP_DST/v2x_fusion/$split/data"
done

echo "[layout] done: $DST"
for split in train val; do
  echo "  $split: $(ls "$COOP_DST/v2x_fusion/$split/data/" | wc -l) scenarios (v2x_fusion -> vehicle-trajectories)"
done
echo "Next:"
echo "  python /deps/DAIR-V2X-Seq/tools/data_converter/maps_merge.py --data_root $DST"
echo "  python traj_match_labels/generate_label.py --data_root $DST --dataset V2X-Seq-TFD"
echo "  PYTHONHASHSEED=0 python preprocess_parallel.py --root $COOP_DST --split val --workers 6   (then --split train)"
