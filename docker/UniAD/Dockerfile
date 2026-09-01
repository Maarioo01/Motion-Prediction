# UniAD (full perception+prediction+planning stack, CVPR 2023 Best Paper)
# https://github.com/opendrivelab/uniad
#
# Adapted from the repo's own official docker/Dockerfile (docker/Dockerfile in this repo)
# rather than reinvented from scratch - it's a tested, working recipe for a notoriously
# rigid OpenMMLab pin (mmcv-full 1.4.0 / mmdet 2.14.0 / mmdet3d 0.17.1). Two changes from
# the original: (1) it git-clones UniAD itself into the image at build time and bakes it
# in; here we instead only prepare the environment and mount the local clone at /workspace
# at runtime, consistent with every other repo in this project (live-editable, and the
# repo dir is already cloned locally by us). (2) minor path adjustments to match that.
#
# Note: Ubuntu 20.04's native apt gcc is gcc-9, which is what CUDA 11.1's nvcc requires -
# no gcc-version override needed here (unlike our other Dockerfiles based on the newer
# Debian-bookworm miniconda3 image, which ships gcc-12 and needs an explicit older-gcc
# install for CUDA 11.x compiles). This is *why* the official recipe doesn't need one.
FROM nvidia/cuda:11.1.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES},compute,display

SHELL [ "/bin/bash", "--login", "-c" ]

# Fixes a GPG key error when apt-get update runs against the NVIDIA CUDA/ML apt repos.
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub \
    && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/7fa2af80.pub

RUN apt-get update -q && \
    apt-get install -q -y \
    wget \
    python3.8-dev \
    python3-pip \
    python3.8-tk \
    git \
    ninja-build \
    ffmpeg libsm6 libxext6 libglib2.0-0 libsm6 libxrender-dev libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0 7.5 8.0+PTX"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"
ENV PATH=${PATH}:/usr/local/cuda:/usr/local/cuda/bin
RUN pip install torch==1.9.1+cu111 torchvision==0.10.1+cu111 torchaudio==0.9.1 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip uninstall numpy scikit-image pandas matplotlib shapely setuptools urllib3 -y
RUN pip install numpy==1.20.0 scikit-image==0.19.3 pandas==1.4.4 matplotlib==3.6 shapely==1.8.5.post1 setuptools==59.5.0
RUN pip install scikit-learn pyquaternion cachetools descartes future tensorboard
RUN pip install IPython

# MMCV-series: prebuilt wheel (mmcv-full) avoids compiling its own CUDA ops from source.
ENV CUDA_HOME=/usr/local/cuda
ENV FORCE_CUDA="1"

RUN pip install mmcv-full==1.4.0 -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.9.0/index.html
RUN pip install mmdet==2.14.0
RUN pip install mmsegmentation==0.14.1

# mmdetection3d IS compiled from source here (iou3d/voxelization/etc custom CUDA ops) -
# this is the step where a gcc/nvcc mismatch would surface, if there were one.
RUN git clone --branch v0.17.1 --single-branch https://github.com/open-mmlab/mmdetection3d.git /mmdetection3d
WORKDIR /mmdetection3d
RUN pip install scipy==1.7.3 scikit-image==0.20.0
RUN pip install --no-cache-dir -v -e .
RUN cp -r /mmdetection3d/mmdet3d /usr/local/lib/python3.8/dist-packages

# UniAD's own requirements.txt (from our local clone - repo itself is mounted at runtime).
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
# torchmetrics gets overridden here on purpose: requirements.txt pins 0.6.2, but UniAD
# actually needs 0.8.2 to run (matches the official Dockerfile's own explicit note).
RUN pip install torchmetrics==0.8.2

RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /workspace
CMD ["/bin/bash"]
