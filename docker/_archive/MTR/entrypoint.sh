#!/bin/bash
set -e

# The repo dir is bind-mounted from the host (owned by the host user), but we run as
# root in-container - git refuses to touch it ("dubious ownership") without this,
# breaking setup.py's git-commit-hash version string.
git config --global --add safe.directory /workspace 2>/dev/null || true

# Build the custom CUDA extensions (mtr/ops/knn, mtr/ops/attention) in-place against
# the (host-mounted) source tree on first start. Safe to skip if already built.
if [ -f "/workspace/setup.py" ]; then
    if ! python -c "from mtr.ops.knn import knn_utils" 2>/dev/null; then
        echo "[entrypoint] Building MTR CUDA extensions (first run)..."
        (cd /workspace && python setup.py develop)
    fi
else
    echo "[entrypoint] WARNING: /workspace does not look like the MTR repo (no setup.py found). Did you mount the repo at /workspace?"
fi

exec "$@"
