#!/bin/bash
set -e

git config --global --add safe.directory /workspace 2>/dev/null || true
git config --global --add safe.directory /workspace/opencood 2>/dev/null || true
git config --global --add safe.directory /workspace/MTR 2>/dev/null || true

# Build the three sub-projects in-place against the host-mounted source tree on first
# run (per docs/env.md): opencood's own package registration, its Cython box_overlaps
# extension (CPU-only), and MTR's CUDA ops (knn/attention, same lineage as TrajFlow).
if [ -f "/workspace/opencood/setup.py" ]; then
    if ! python -c "import opencood" 2>/dev/null; then
        echo "[entrypoint] Installing opencood (first run)..."
        (cd /workspace && python opencood/setup.py develop)
    fi
    if [ ! -f "/workspace/opencood/utils/box_overlaps"*.so ] 2>/dev/null; then
        echo "[entrypoint] Building opencood's box_overlaps Cython extension (first run)..."
        (cd /workspace && python opencood/utils/setup.py build_ext --inplace)
    fi
else
    echo "[entrypoint] WARNING: /workspace/opencood not found. Did you mount the repo at /workspace?"
fi

if [ -f "/workspace/MTR/setup.py" ]; then
    if ! python -c "from mtr.ops.knn import knn_utils" 2>/dev/null; then
        echo "[entrypoint] Building MTR CUDA extensions (first run)..."
        (cd /workspace/MTR && python setup.py develop)
    fi
fi

exec "$@"
