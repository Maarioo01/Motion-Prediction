#!/bin/bash
# Writable layout for V2X-Graph on V2X-Traj, as symlinks into the read-only dataset mount.
# Run inside the v2x-graph container:  bash prepare_v2xtraj_layout.sh
#
# The release already has <view>/<split>/data/*.csv and prebuilt map_files/ (no
# maps_merge needed). Missing: a writable root for traj_match_labels/ and the .pt caches,
# and the 'v2x_test' folder that V2XTrajDataset reads as its raw (ego) view - in
# process_argoverse that file is read as ego_df next to the infrastructure and vehicle
# views, so it is linked to ego-trajectories.
set -euo pipefail
SRC=${1:-/data/v2x-traj}
DST=${2:-/workspace/data_staging/v2x-traj}

[ -d "$SRC/ego-trajectories" ] || { echo "no V2X-Traj at $SRC"; exit 1; }
mkdir -p "$DST"
for d in ego-trajectories infrastructure-trajectories vehicle-trajectories traffic-light maps map_files; do
  ln -sfn "$SRC/$d" "$DST/$d"
done
for split in train val; do
  mkdir -p "$DST/v2x_test/$split" "$DST/traj_match_labels/$split/data"
  ln -sfn "$SRC/ego-trajectories/$split/data" "$DST/v2x_test/$split/data"
done

echo "[layout] done: $DST"
for split in train val; do
  echo "  $split: $(ls "$DST/v2x_test/$split/data/" | wc -l) scenarios (v2x_test -> ego-trajectories)"
done
echo "Next (DATA_ROOT=$DST so dair_map_api reads the V2X-Traj map_files):"
echo "  cd traj_match_labels && python generate_label.py --data_root $DST --dataset V2X-Traj"
echo "  PYTHONHASHSEED=0 python preprocess_parallel.py --dataset V2X-Traj --root $DST --split val --workers 6   (then --split train)"
