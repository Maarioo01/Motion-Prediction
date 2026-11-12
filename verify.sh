#!/bin/bash
# Runs a quick import + CUDA sanity check inside each service's container - the same
# checks used to originally validate each build. Not a full model test, just proof the
# environment (torch/CUDA, compiled extensions, key libraries) is intact.
#
# Usage:
#   ./verify.sh                 # check all active services
#   ./verify.sh qcnet           # check just this one
#
# Checks for archived services are kept in docker/_archive/README.md.
set -uo pipefail
cd "$(dirname "$0")"

declare -A CHECKS=(
  [qcnet]="python -c \"import torch, torch_geometric, torch_scatter, torch_cluster, pytorch_lightning, av2; assert torch.cuda.is_available()\""
  [v2x-graph]="python -c \"import torch, torch_geometric, pytorch_lightning, torchmetrics, lap, shapely, scipy, cv2; from torch_geometric.nn import MessagePassing; from dair_map_api import DAIRV2XMap; from argoverse.utils.centerline_utils import centerline_to_polygon; assert torch.__version__=='1.12.1+cu116'; assert torch.cuda.is_available(); x=torch.randn(4,8).cuda(); print(torch.cuda.get_device_name(0), (x@x.T).sum().item())\""
  [cmp]="python -c \"import torch, torchvision, torch_geometric, spconv, opencood; from mtr.ops.knn import knn_utils; assert torch.cuda.is_available()\""
)

SERVICES=("$@")
if [ "${#SERVICES[@]}" -eq 0 ]; then
  SERVICES=(qcnet cmp v2x-graph)
fi

overall=0
for svc in "${SERVICES[@]}"; do
  printf "%-22s " "$svc"
  if [ -z "${CHECKS[$svc]+x}" ]; then
    echo "SKIPPED (no check defined for '$svc')"
    continue
  fi
  logfile="/tmp/verify_${svc}.log"
  if docker compose run --rm "$svc" bash -c "${CHECKS[$svc]}" > "$logfile" 2>&1; then
    echo "OK"
  else
    echo "FAILED (see $logfile)"
    overall=1
  fi
done

exit $overall
