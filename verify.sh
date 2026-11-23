#!/bin/bash
# Runs a quick import + CUDA sanity check inside each service's container - the same
# checks used to originally validate each build. Not a full model test, just proof the
# environment (torch/CUDA, compiled extensions, key libraries) is intact.
#
# Usage:
#   ./verify.sh                 # check all active services
#   ./verify.sh qcnet           # check just this one
#
# The original images (qcnet, cmp, v2x-graph) only run on GPU 0 (RTX 3090). The *-cu128
# images run on both cards and are checked on each: GPU 0 (3090) and GPU 1 (5090).
#
# Checks for archived services are kept in docker/_archive/README.md.
set -uo pipefail
cd "$(dirname "$0")"

declare -A CHECKS=(
  [qcnet]="python -c \"import torch, torch_geometric, torch_scatter, torch_cluster, pytorch_lightning, av2; assert torch.cuda.is_available()\""
  [v2x-graph]="python -c \"import torch, torch_geometric, pytorch_lightning, torchmetrics, lap, shapely, scipy, cv2; from torch_geometric.nn import MessagePassing; from dair_map_api import DAIRV2XMap; from argoverse.utils.centerline_utils import centerline_to_polygon; assert torch.__version__=='1.12.1+cu116'; assert torch.cuda.is_available(); x=torch.randn(4,8).cuda(); print(torch.cuda.get_device_name(0), (x@x.T).sum().item())\""
  [qcnet-cu128]="python -c \"import torch, torch_geometric, torch_scatter, torch_cluster, pytorch_lightning, av2; from torch_cluster import radius_graph; assert torch.__version__=='2.7.1+cu128'; assert torch.cuda.is_available(); x=torch.randn(1000,2).cuda(); print(torch.cuda.get_device_name(0), radius_graph(x, r=0.2).shape[1])\""
  [v2x-graph-cu128]="python -c \"import torch, torch_geometric, pytorch_lightning, torchmetrics, lap, shapely, scipy, cv2; from torch_geometric.nn import MessagePassing; from dair_map_api import DAIRV2XMap; from argoverse.utils.centerline_utils import centerline_to_polygon; assert torch.__version__=='2.7.1+cu128'; assert torch.cuda.is_available(); x=torch.randn(4,8).cuda(); print(torch.cuda.get_device_name(0), (x@x.T).sum().item())\""
  [cmp]="python -c \"import torch, torchvision, torch_geometric, spconv, opencood; from mtr.ops.knn import knn_utils; assert torch.cuda.is_available()\""
)

SERVICES=("$@")
if [ "${#SERVICES[@]}" -eq 0 ]; then
  SERVICES=(qcnet cmp v2x-graph qcnet-cu128 v2x-graph-cu128)
fi

overall=0
for svc in "${SERVICES[@]}"; do
  if [ -z "${CHECKS[$svc]+x}" ]; then
    printf "%-22s SKIPPED (no check defined for '%s')\n" "$svc" "$svc"
    continue
  fi
  case "$svc" in
    *-cu128) gpus=(0 1) ;;   # either card
    *)       gpus=(0) ;;     # 3090 only (compose pins these to GPU 0 anyway)
  esac
  for gpu in "${gpus[@]}"; do
    printf "%-22s " "$svc (GPU $gpu)"
    logfile="/tmp/verify_${svc}_gpu${gpu}.log"
    if GPU=$gpu docker compose run --rm --no-deps "$svc" bash -c "${CHECKS[$svc]}" > "$logfile" 2>&1; then
      echo "OK   $(grep -E 'RTX|GeForce|NVIDIA' "$logfile" | tail -1)"
    else
      echo "FAILED (see $logfile)"
      overall=1
    fi
  done
done

exit $overall
