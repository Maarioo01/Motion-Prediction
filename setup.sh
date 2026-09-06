#!/bin/bash
# Clones each upstream model repo into repos/<name> (skipping the clone if it's already
# there) and overlays this project's Dockerfile/entrypoint.sh/requirements onto it. The
# repos/ directory itself is gitignored - upstream source isn't redistributed through
# this repo, only fetched fresh from the original authors.
#
# Usage:
#   ./setup.sh          # clone + overlay the 10 working repos
#   ./setup.sh --all    # also clone the 2 repos that were investigated but not built
#                        # (StreamingForecasting, V2I_trajectory_prediction - see README)
set -e
cd "$(dirname "$0")"

declare -A REPOS=(
  ["QCNet"]="https://github.com/ZikangZhou/QCNet.git"
  ["RealMotion"]="https://github.com/fudan-zvg/RealMotion.git"
  ["TrajFlow"]="https://github.com/DSL-Lab/TrajFlow.git"
  ["SceneInformer"]="https://github.com/sisl/SceneInformer.git"
  ["emp"]="https://github.com/a-pru/emp.git"
  ["pretraining-synthetic"]="https://github.com/yhli123/Pretraining_on_Synthetic_Driving_Data_for_Trajectory_Prediction.git"
  ["GameFormer"]="https://github.com/MCZhi/GameFormer.git"
  ["UniAD"]="https://github.com/opendrivelab/uniad.git"
  ["CMP"]="https://github.com/tasl-lab/CMP.git"
  ["UniTraj"]="https://github.com/vita-epfl/UniTraj.git"
)

declare -A EXTRA_REPOS=(
  ["StreamingForecasting"]="https://github.com/ziqipang/StreamingForecasting.git"
  ["V2I_trajectory_prediction"]="https://github.com/xichennn/V2I_trajectory_prediction.git"
)

clone_and_overlay() {
  local name="$1" url="$2"
  if [ -d "repos/$name/.git" ]; then
    echo "[setup] repos/$name already cloned, skipping clone"
  else
    echo "[setup] cloning $name..."
    git clone --depth 1 "$url" "repos/$name"
  fi
  if [ -f "docker/$name/Dockerfile" ]; then
    echo "[setup] overlaying docker/$name onto repos/$name"
    cp "docker/$name/Dockerfile" "repos/$name/Dockerfile"
    if [ -f "docker/$name/entrypoint.sh" ]; then
      cp "docker/$name/entrypoint.sh" "repos/$name/entrypoint.sh"
    fi
    if [ -f "docker/$name/requirements-docker.txt" ]; then
      cp "docker/$name/requirements-docker.txt" "repos/$name/requirements.txt"
    fi
  fi
}

# Some repos have real bugs in their own source (not just environment/dependency
# issues), fixed in place and preserved here so a fresh `setup.sh` run doesn't have to
# rediscover them - see docker/<name>/patches/ and docs/BUILD_GOTCHAS.md for what/why.
apply_patches() {
  local name="$1"
  [ -d "docker/$name/patches" ] || return 0
  case "$name" in
    SceneInformer)
      echo "[setup] applying docker/SceneInformer/patches (protobuf bytes fix, DDP strategy fix, filled-in config paths - see BUILD_GOTCHAS.md)"
      cp "docker/SceneInformer/patches/waymo_utils.py" "repos/SceneInformer/sceneinformer/utils/waymo_utils.py"
      cp "docker/SceneInformer/patches/train_lightning.py" "repos/SceneInformer/scripts/train_lightning.py"
      cp "docker/SceneInformer/patches/scene_informer.yaml" "repos/SceneInformer/configs/scene_informer.yaml"
      cp "docker/SceneInformer/patches/scene_informer_smoketest.yaml" "repos/SceneInformer/configs/scene_informer_smoketest.yaml"
      ;;
    GameFormer)
      echo "[setup] applying docker/GameFormer/patches (objects_of_interest/tracks_to_predict KeyError fix - see BUILD_GOTCHAS.md)"
      cp "docker/GameFormer/patches/data_process.py" "repos/GameFormer/interaction_prediction/data_process.py"
      ;;
  esac
}

mkdir -p repos
for name in "${!REPOS[@]}"; do
  clone_and_overlay "$name" "${REPOS[$name]}"
  apply_patches "$name"
done

if [ "$1" == "--all" ]; then
  for name in "${!EXTRA_REPOS[@]}"; do
    clone_and_overlay "$name" "${EXTRA_REPOS[$name]}"
  done
fi

echo "[setup] done. Build images with: docker compose build"
