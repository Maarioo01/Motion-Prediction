#!/bin/bash
set -e
git config --global --add safe.directory /workspace 2>/dev/null || true

# The released checkpoints are Git LFS objects; a plain clone only has 133-byte pointer
# files and the host has no git-lfs. Fetch them once, then hand them back to the host
# user that owns the bind-mounted repo (containers run as root).
if [ -d /workspace/checkpoints ] && \
   find /workspace/checkpoints -name '*.ckpt' -size -1024c | grep -q .; then
    echo "[entrypoint] Fetching V2X-Graph checkpoints via git lfs (first run)..."
    (cd /workspace && git lfs install --local >/dev/null && git lfs pull)
    chown -R "$(stat -c %u:%g /workspace)" /workspace/checkpoints /workspace/.git
fi

exec "$@"
