# SceneInformer (top 9, ICRA 2024) - https://github.com/sisl/SceneInformer
# No custom CUDA extensions - pure pip/conda env, so no nvcc/gcc-version dance needed.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n sceneinformer python=3.10.12 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "sceneinformer", "/bin/bash", "-c"]

# waymo-open-dataset-tf pulls TensorFlow; installed before the pinned torch triplet
# (installing torch first then extra requirements after has, elsewhere in this project,
# silently swapped it for a different build via pip's resolver - always pin torch last).
RUN pip install --no-cache-dir waymo-open-dataset-tf-2-12-0==1.6.4

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# pytorch-lightning/lightning in requirements.txt pull an unpinned transitive "torch"
# dependency, which happened to resolve to the exact same bare version (2.0.1) from
# default PyPI (cu117-tagged) before this step runs. Because the bare version string
# already matched, pip considered `torch==2.0.1` "already satisfied" and skipped
# reinstalling it here, only fetching torchvision fresh - leaving mismatched CUDA
# builds (torch cu117 vs torchvision cu118). Pinning the explicit +cu118 local version
# forces a real (re)install of the correct build regardless of what's already present.
RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

RUN echo "conda activate sceneinformer" >> /root/.bashrc
ENV PATH=/opt/conda/envs/sceneinformer/bin:$PATH

WORKDIR /workspace
CMD ["/bin/bash"]
