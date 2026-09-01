# CMP: Cooperative Motion Prediction with Multi-Agent Communication (top 10)
# https://github.com/tasl-lab/CMP
# A full V2X cooperative pipeline, not a single model: wires together OpenCOOD (LiDAR
# cooperative detection), AB3Dmot (multi-object tracking) and MTR (trajectory
# prediction, same lineage as TrajFlow/UniTraj's CUDA ops). Needs OPV2V + V2V4Real
# datasets, neither present on /raid - this Dockerfile only prepares the environment.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    ffmpeg libsm6 libxext6 libglib2.0-0 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n cmp python=3.7.11 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "cmp", "/bin/bash", "-c"]

# environment.yml + requirements.txt + opencood/requirements.txt merged (minus torch/
# torchvision/torch-geometric, handled separately below).
COPY requirements-docker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN pip install --no-cache-dir spconv-cu117

# nvcc + compatible host gcc for MTR's CUDA ops (env.yml's own commented notes already
# point at this exact fix: gxx<=11.5.0 for CUDA 11.7 - matches our gcc-11 lesson from
# TrajFlow/RealMotion/UniTraj).
RUN conda install -y -c "nvidia/label/cuda-11.7.0" cuda-toolkit=11.7 \
    && conda install -y -c conda-forge ninja gcc=11 gxx=11 \
    && conda clean -afy

RUN pip install --no-cache-dir \
    torch==1.13.1+cu117 torchvision==0.14.1+cu117 \
    --index-url https://download.pytorch.org/whl/cu117

RUN pip install --no-cache-dir torch-geometric==2.3.1

ENV TORCH_CUDA_ARCH_LIST="8.6"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN echo "conda activate cmp" >> /root/.bashrc
ENV PATH=/opt/conda/envs/cmp/bin:$PATH

# Path-based sub-packages (no install step) per docs/env.md.
ENV PYTHONPATH="/workspace/AB3Dmot:/workspace/AB3Dmot/Xinshuo_PyToolbox:/workspace/MTR:/workspace/opencood:${PYTHONPATH}"

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
