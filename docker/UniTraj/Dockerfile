# UniTraj (top 2, "only environment" per the user's own notes on the source PDF) -
# https://github.com/vita-epfl/UniTraj
# A framework, not a single model: bundles AutoBot/MTR/Wayformer/SMART/Forecast-MAE/EMP
# backbones behind one training/eval harness, gated behind the separate ScenarioNet
# data-conversion toolkit. AGPLv3 licensed.
#
# requirements.txt leaves torch and natten unpinned. Rather than let pip float to
# whatever's currently latest (risky: UniTraj's own setup.py compiles the same
# MTR-derived CUDA ops as TrajFlow, and natten's source build isn't guaranteed
# backward-compatible with an arbitrarily new torch's C++ API), we reuse the exact
# torch 2.0.1+cu118 / natten 0.17.3 combo already proven to compile cleanly from
# source on this machine's GPUs (see RealMotion's Dockerfile + README gotchas).
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
# libgl1/libglib2.0-0/etc: metadrive (ScenarioNet's dependency) pulls regular
# opencv-python (not headless), which needs libGL.so.1 - not present on a minimal
# image (see README "Build gotchas").
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    ffmpeg libsm6 libxext6 libglib2.0-0 libxrender-dev libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n unitraj python=3.9 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "unitraj", "/bin/bash", "-c"]

# ScenarioNet (dataset unification toolkit UniTraj depends on) + its MetaDrive dependency.
RUN pip install --no-cache-dir "metadrive-simulator>=0.4.1.1" \
    && pip install --no-cache-dir git+https://github.com/metadriverse/scenarionet.git

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# nvcc + a compatible host gcc for compiling natten and UniTraj's own MTR-derived CUDA
# ops against cu118 (see README "Build gotchas": CUDA 11.8's nvcc rejects gcc>11, and
# this base image's apt gcc is gcc-12).
RUN conda install -y -c "nvidia/label/cuda-11.8.0" cuda-toolkit=11.8 \
    && conda install -y -c conda-forge ninja gcc=11 gxx=11 \
    && conda clean -afy

RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# The SMART backbone's dataset module imports torch_geometric at package-init time
# (triggered just by importing unitraj.models), not listed in requirements.txt at all.
# Same torch_geometric/torch-2.0.0+cu118 combo already proven with QCNet.
RUN pip install --no-cache-dir torch_geometric==2.3.0 \
    && pip install --no-cache-dir torch_scatter==2.1.1 torch_sparse==0.6.17 torch_cluster==1.6.1 \
       -f https://data.pyg.org/whl/torch-2.0.0+cu118.html

ENV TORCH_CUDA_ARCH_LIST="8.6"
ENV FORCE_CUDA="1"
ENV NATTEN_CUDA_ARCH="8.6"
# setuptools>=81 dropped pkg_resources, which torch 2.0.1's cpp_extension.py still
# imports from - pin to a pre-removal version for the natten build.
RUN pip install --no-cache-dir ninja packaging wheel "setuptools==69.5.1"
RUN pip install --no-cache-dir --no-build-isolation natten==0.17.3

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN echo "conda activate unitraj" >> /root/.bashrc
ENV PATH=/opt/conda/envs/unitraj/bin:$PATH

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
