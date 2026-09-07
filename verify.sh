#!/bin/bash
# Runs a quick import + CUDA sanity check inside each service's container - the same
# checks used to originally validate each build. Not a full model test, just proof the
# environment (torch/CUDA, compiled extensions, key libraries) is intact.
#
# Usage:
#   ./verify.sh                 # check all 10 services
#   ./verify.sh qcnet unitraj   # check just these
set -uo pipefail
cd "$(dirname "$0")"

declare -A CHECKS=(
  [qcnet]="python -c \"import torch, torch_geometric, torch_scatter, torch_cluster, pytorch_lightning, av2; assert torch.cuda.is_available()\""
  [realmotion]="python -c \"import torch, torchvision, natten, av2, pytorch_lightning; from natten import NeighborhoodAttention1D; import torch as t; na=NeighborhoodAttention1D(dim=32,num_heads=4,kernel_size=7).cuda(); na(t.randn(2,16,32).cuda()); assert torch.cuda.is_available()\""
  [trajflow]="python -c \"import torch, trajflow, waymo_open_dataset; from trajflow.mtr_ops.knn import knn_utils; assert torch.cuda.is_available()\""
  [sceneinformer]="python -c \"import torch, torchvision, waymo_open_dataset, pytorch_lightning; assert torch.cuda.is_available()\""
  [emp]="python -c \"import torch, torchvision, av2, pytorch_lightning, timm; assert torch.cuda.is_available()\""
  [pretraining-synthetic]="python -c \"import torch, sys; sys.path.insert(0,'src'); import utils_cython; from argoverse.map_representation.map_api import ArgoverseMap; from argoverse.evaluation import eval_forecasting; assert torch.cuda.is_available()\""
  [gameformer]="python -c \"import torch, waymo_open_dataset, shapely; assert torch.cuda.is_available()\""
  [uniad]="python -c \"import torch, torchvision, mmcv, mmdet, mmdet3d, torchmetrics; from mmdet3d.ops import ball_query; assert torch.cuda.is_available()\""
  [cmp]="python -c \"import torch, torchvision, torch_geometric, spconv, opencood; from mtr.ops.knn import knn_utils; assert torch.cuda.is_available()\""
  [unitraj]="python -c \"import torch, natten, av2, pytorch_lightning, hydra, timm, torch_geometric, scenarionet; assert torch.cuda.is_available()\""
  [mtr]="python -c \"import torch, waymo_open_dataset; from mtr.ops.knn import knn_utils; from mtr.ops.attention import attention_utils; assert torch.cuda.is_available()\""
)

SERVICES=("$@")
if [ "${#SERVICES[@]}" -eq 0 ]; then
  SERVICES=(qcnet realmotion trajflow sceneinformer emp pretraining-synthetic gameformer uniad cmp unitraj mtr)
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
