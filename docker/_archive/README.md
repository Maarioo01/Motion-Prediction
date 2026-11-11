# Archived Docker configs

These configs were removed from the active bench on 2026-11-10 (Phase 0 checklist item B1)
because they are not part of the V2X plan (see `CLAUDE.md`, "Methods"). They all built and
passed `verify.sh` before archiving; the build notes are still in `docs/BUILD_GOTCHAS.md`.

`setup.sh`, `verify.sh` and `docker-compose.yml` no longer know about them. Nothing here is
built or run unless explicitly asked for (RealMotion may come back for paper 2).

| Name | Upstream | Dataset it used |
| --- | --- | --- |
| RealMotion | https://github.com/fudan-zvg/RealMotion.git | Argoverse 2 |
| TrajFlow | https://github.com/DSL-Lab/TrajFlow.git | Waymo |
| SceneInformer | https://github.com/sisl/SceneInformer.git | Waymo (`training_20s`) |
| emp | https://github.com/a-pru/emp.git | Argoverse 2 |
| pretraining-synthetic | https://github.com/yhli123/Pretraining_on_Synthetic_Driving_Data_for_Trajectory_Prediction.git | Argoverse 1.1 + bundled synthetic data |
| GameFormer | https://github.com/MCZhi/GameFormer.git | Waymo |
| UniAD | https://github.com/opendrivelab/uniad.git | nuScenes |
| UniTraj | https://github.com/vita-epfl/UniTraj.git | Waymo / nuScenes / Argoverse 2 |
| MTR | https://github.com/sshaoshuai/MTR.git | Waymo |

`StreamingForecasting` (https://github.com/ziqipang/StreamingForecasting.git) was also
dropped from `setup.sh --all`; it was never built.

## Restoring one

1. `git mv docker/_archive/<Name> docker/<Name>`
2. Add `["<Name>"]="<url>"` to `REPOS` in `setup.sh`, plus its patch rule below if it has one.
3. Paste its block from [`docker-compose.archive.yml`](docker-compose.archive.yml) back into
   `docker-compose.yml` (check it still pins `device_ids: ["0"]`).
4. Add its check below to `CHECKS` in `verify.sh`.
5. `./setup.sh && docker compose build <service> && ./verify.sh <service>`

## Patch rules (were in `setup.sh` `apply_patches`)

```bash
    SceneInformer)
      echo "[setup] applying docker/SceneInformer/patches (protobuf bytes fix, DDP strategy fix, filled-in config paths - see BUILD_GOTCHAS.md)"
      cp "docker/SceneInformer/patches/waymo_utils.py" "repos/SceneInformer/sceneinformer/utils/waymo_utils.py"
      cp "docker/SceneInformer/patches/train_lightning.py" "repos/SceneInformer/scripts/train_lightning.py"
      cp "docker/SceneInformer/patches/scene_informer.yaml" "repos/SceneInformer/configs/scene_informer.yaml"
      cp "docker/SceneInformer/patches/scene_informer_smoketest.yaml" "repos/SceneInformer/configs/scene_informer_smoketest.yaml"
      cp "docker/SceneInformer/patches/generate_dataset_summary.py" "repos/SceneInformer/scripts/generate_dataset_summary.py"
      ;;
    GameFormer)
      echo "[setup] applying docker/GameFormer/patches (objects_of_interest/tracks_to_predict KeyError fix - see BUILD_GOTCHAS.md)"
      cp "docker/GameFormer/patches/data_process.py" "repos/GameFormer/interaction_prediction/data_process.py"
      ;;
    MTR)
      echo "[setup] applying docker/MTR/patches (protobuf bytes fix + missing driveway map-feature type - see BUILD_GOTCHAS.md)"
      cp "docker/MTR/patches/data_preprocess.py" "repos/MTR/mtr/datasets/waymo/data_preprocess.py"
      cp "docker/MTR/patches/waymo_types.py" "repos/MTR/mtr/datasets/waymo/waymo_types.py"
      ;;
```

## `verify.sh` checks

```bash
  [realmotion]="python -c \"import torch, torchvision, natten, av2, pytorch_lightning; from natten import NeighborhoodAttention1D; import torch as t; na=NeighborhoodAttention1D(dim=32,num_heads=4,kernel_size=7).cuda(); na(t.randn(2,16,32).cuda()); assert torch.cuda.is_available()\""
  [trajflow]="python -c \"import torch, trajflow, waymo_open_dataset; from trajflow.mtr_ops.knn import knn_utils; assert torch.cuda.is_available()\""
  [sceneinformer]="python -c \"import torch, torchvision, waymo_open_dataset, pytorch_lightning; assert torch.cuda.is_available()\""
  [emp]="python -c \"import torch, torchvision, av2, pytorch_lightning, timm; assert torch.cuda.is_available()\""
  [pretraining-synthetic]="python -c \"import torch, sys; sys.path.insert(0,'src'); import utils_cython; from argoverse.map_representation.map_api import ArgoverseMap; from argoverse.evaluation import eval_forecasting; assert torch.cuda.is_available()\""
  [gameformer]="python -c \"import torch, waymo_open_dataset, shapely; assert torch.cuda.is_available()\""
  [uniad]="python -c \"import torch, torchvision, mmcv, mmdet, mmdet3d, torchmetrics; from mmdet3d.ops import ball_query; assert torch.cuda.is_available()\""
  [unitraj]="python -c \"import torch, natten, av2, pytorch_lightning, hydra, timm, torch_geometric, scenarionet; assert torch.cuda.is_available()\""
  [mtr]="python -c \"import torch, waymo_open_dataset; from mtr.ops.knn import knn_utils; from mtr.ops.attention import attention_utils; assert torch.cuda.is_available()\""
```

## What stays on disk

Archiving only touches tracked config. The cloned sources in `repos/<Name>/`, the built
images (`motion-prediction/<name>:latest`) and the staging folders under `/raid/scratch/`
are still there; removing them is a separate, confirmed step (checklist A3).
