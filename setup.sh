#!/bin/bash
# Clones each upstream model repo into repos/<name> (skipping the clone if it's already
# there) and overlays this project's Dockerfile/entrypoint.sh/requirements onto it. The
# repos/ directory itself is gitignored - upstream source isn't redistributed through
# this repo, only fetched fresh from the original authors.
#
# Usage:
#   ./setup.sh          # clone + overlay the active repos (QCNet, CMP, V2X-Graph, DAIR-V2X-Seq)
#   ./setup.sh --all    # also clone repos that are planned but not built yet
#                        # (V2I_trajectory_prediction - checklist B3)
#
# Archived configs (not cloned here) live in docker/_archive/ - see its README.md.
set -e
cd "$(dirname "$0")"

declare -A REPOS=(
  ["QCNet"]="https://github.com/ZikangZhou/QCNet.git"
  ["CMP"]="https://github.com/tasl-lab/CMP.git"
  ["V2X-Graph"]="https://github.com/AIR-THU/V2X-Graph.git"
  # No image of its own: mounted into v2x-graph for its dataset/map API and map-merge
  # tool, and the source of the HiVT baseline plugin (checklist B5).
  ["DAIR-V2X-Seq"]="https://github.com/AIR-THU/DAIR-V2X-Seq.git"
)

declare -A EXTRA_REPOS=(
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
  # Project-added scripts (not upstream code, not fixes) - e.g. docker/QCNet/extras/qcnet_inference.py
  if [ -d "docker/$name/extras" ]; then
    echo "[setup] copying docker/$name/extras into repos/$name"
    cp "docker/$name/extras/"* "repos/$name/"
  fi
}

# Some repos have real bugs in their own source (not just environment/dependency
# issues), fixed in place and preserved here so a fresh `setup.sh` run doesn't have to
# rediscover them - see docker/<name>/patches/ and docs/BUILD_GOTCHAS.md for what/why.
apply_patches() {
  local name="$1"
  [ -d "docker/$name/patches" ] || return 0
  case "$name" in
    # <Name>)
    #   echo "[setup] applying docker/<Name>/patches (... - see BUILD_GOTCHAS.md)"
    #   cp "docker/<Name>/patches/<file>" "repos/<Name>/<path>/<file>"
    #   ;;
    *)
      echo "[setup] WARNING: docker/$name/patches exists but setup.sh has no rule for it"
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
