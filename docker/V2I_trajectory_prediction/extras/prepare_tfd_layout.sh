#!/bin/bash
# Writable V2X-Seq-TFD layout for V2INet (checklist B3). Run inside the v2inet-cu128 container.
#
# V2INet's V2XDataset (datasets/v2x_dataset.py) uses --root = <...>/vehicle-trajectories and reads
#   <root>/<split>/*.csv                                      car view (scenario list)
#   <root>/../infrastructure-trajectories/<split>/*.csv       roadside view
#   $DATA_ROOT/map_files/yizhuang_PEK_*                      merged map (maps_merge.py output)
# and writes <root>/<split>/v2x_processed/*.pt next to the CSVs. The release already has that
# folder layout but is mounted read-only, so the car CSVs become per-file symlinks in a writable
# tree; the roadside folder is one directory symlink. No CSV is copied or changed.
#
# Usage: bash prepare_tfd_layout.sh [TFD root, default /data/v2x-seq-tfd] [dest, default /workspace/data_staging/tfd]
set -e
SRC=${1:-/data/v2x-seq-tfd}
DST=${2:-/workspace/data_staging/tfd}
C=cooperative-vehicle-infrastructure

mkdir -p "$DST/$C"
ln -sfn "$SRC/$C/infrastructure-trajectories" "$DST/$C/infrastructure-trajectories"
for s in train val; do
  d="$DST/$C/vehicle-trajectories/$s"
  mkdir -p "$d"
  find "$SRC/$C/vehicle-trajectories/$s" -maxdepth 1 -name '*.csv' -exec ln -sf -t "$d" {} +
  echo "[layout] $s: $(find "$d" -maxdepth 1 -name '*.csv' | wc -l) car-view CSVs linked"
done
if [ ! -f "$DST/map_files/yizhuang_PEK_vector_map.json" ]; then
  echo "[layout] WARNING: $DST/map_files is missing. Copy the merged map made by DAIR-V2X-Seq's"
  echo "         tools/data_converter/maps_merge.py (e.g. /raid/scratch/v2xgraph_data/tfd/map_files)."
fi
