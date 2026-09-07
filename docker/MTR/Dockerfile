# MTR (Motion Transformer): https://github.com/sshaoshuai/MTR
# NeurIPS 2022 oral, won the WOMD Motion Prediction Challenge 2022. Included here as
# the canonical reference implementation, not for novelty - it's the baseline nearly
# every other repo in this bench compares against (QCNet/RealMotion/TrajFlow/GameFormer/
# emp all report MTR numbers, UniTraj bundles it as one of its 6 backbones, and CMP's
# own prediction stage is an MTR-based module) - see docs/MODELS_OVERVIEW.md for why
# this one was added over its unreleased MTR++ successor (paper published, code never
# released - confirmed by checking the actual repo contents, not just the README).
#
# Same custom CUDA ops (knn_cuda, attention_cuda) that TrajFlow's data_preprocess.py
# is explicitly derived from, and that UniTraj vendors internally - already proven to
# compile cleanly on this machine (see UniTraj/TrajFlow's own Dockerfile notes), so
# this recipe reuses their proven torch 2.2.0+cu118 / gcc-11 combo rather than MTR's
# own (much older, Python 3.8 / TF 2.6.0) documented recipe, which would reintroduce
# the numpy~=1.19.2 conflict already solved differently for CMP.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n mtr python=3.10 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "mtr", "/bin/bash", "-c"]

# Modern TF/waymo-open-dataset build (not the ancient 2.6.0 from MTR's own docs) -
# same version TrajFlow already uses successfully for the same scenario-protobuf
# preprocessing task in this project.
RUN pip install --no-cache-dir waymo-open-dataset-tf-2-12-0

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# torch/torchvision/torchaudio last and re-pinned, for the same reason documented in
# TrajFlow's Dockerfile: an earlier unpinned "torch" requirement from another package
# can silently swap this for a plain (non +cu118) PyPI build otherwise.
RUN pip install --no-cache-dir \
    torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 \
    --index-url https://download.pytorch.org/whl/cu118

# nvcc matching the cu118 torch build + gcc 11 (CUDA 11.8 rejects gcc>11), for
# compiling mtr/ops/{knn,attention}'s custom CUDA extensions.
RUN conda install -y -c "nvidia/label/cuda-11.8.0" cuda-toolkit=11.8 \
    && conda install -y -c conda-forge ninja git gcc=11 gxx=11 \
    && conda clean -afy

ENV TORCH_CUDA_ARCH_LIST="8.6"
ENV PATH=/opt/conda/envs/mtr/bin:$PATH
RUN echo "conda activate mtr" >> /root/.bashrc

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
