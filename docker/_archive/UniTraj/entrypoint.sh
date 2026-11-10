#!/bin/bash
set -e

git config --global --add safe.directory /workspace 2>/dev/null || true

# Build UniTraj's own CUDA extensions (MTR-derived knn/attention ops) in-place against
# the host-mounted source tree on first run, same reasoning as TrajFlow's entrypoint.
# Checked via direct .so existence, NOT `python -c "from unitraj.models... import ..."`:
# importing unitraj.models at all cascades through its __init__.py into every bundled
# backbone including fmae, whose trainer_forecast.py has an upstream bug (bare
# `from utils.submission_av2 import ...` instead of `from unitraj.utils...`) that only
# resolves when running as `cd unitraj && python train.py`, not as an installed package -
# an import-based check would treat that unrelated bug as "extension not built" and
# needlessly recompile on every container start.
if [ -f "/workspace/setup.py" ]; then
    if [ ! -f /workspace/unitraj/models/mtr/ops/knn/knn_cuda*.so ] || [ ! -f /workspace/unitraj/models/mtr/ops/attention/attention_cuda*.so ]; then
        echo "[entrypoint] Building UniTraj CUDA extensions (first run)..."
        (cd /workspace && python setup.py develop)
    fi
else
    echo "[entrypoint] WARNING: /workspace does not look like the UniTraj repo (no setup.py found). Did you mount the repo at /workspace?"
fi

exec "$@"
