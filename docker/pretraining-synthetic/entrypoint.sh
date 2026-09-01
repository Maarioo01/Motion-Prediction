#!/bin/bash
set -e

git config --global --add safe.directory /workspace 2>/dev/null || true

# Build the Cython extension in-place against the (host-mounted) source tree on first
# run, same reasoning as TrajFlow's CUDA-ops entrypoint.
if [ -f "/workspace/src/utils_cython.pyx" ]; then
    if ! python -c "import sys; sys.path.insert(0, '/workspace/src'); import utils_cython" 2>/dev/null; then
        echo "[entrypoint] Building utils_cython extension (first run)..."
        (cd /workspace/src && cython -a utils_cython.pyx && python setup.py build_ext --inplace)
    fi
else
    echo "[entrypoint] WARNING: /workspace does not look like this repo (no src/utils_cython.pyx found). Did you mount the repo at /workspace?"
fi

exec "$@"
