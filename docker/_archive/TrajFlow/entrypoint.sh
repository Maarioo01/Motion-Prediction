#!/bin/bash
set -e

# The repo dir is bind-mounted from the host (owned by the host user), but we run as
# root in-container - git refuses to touch it ("dubious ownership") without this,
# which breaks setup_trajflow.py's git-commit-hash version string (empty hash ->
# invalid PEP 440 version -> setuptools crash).
git config --global --add safe.directory /workspace 2>/dev/null || true

# Build the custom CUDA extensions in-place against the (host-mounted) source tree
# on first start, or whenever the source has no compiled .so yet. Safe to skip if
# already built (e.g. container restarted without the image changing).
if [ -f "/workspace/setup/setup_trajflow.py" ]; then
    if ! python -c "from trajflow.mtr_ops.knn import knn_utils" 2>/dev/null; then
        echo "[entrypoint] Building TrajFlow CUDA extensions (first run)..."
        (cd /workspace && python setup/setup_trajflow.py develop)
    fi
else
    echo "[entrypoint] WARNING: /workspace does not look like the TrajFlow repo (no setup/setup_trajflow.py found). Did you mount the repo at /workspace?"
fi

exec "$@"
