# QCNet (top 1, Argoverse leaderboards) - https://github.com/ZikangZhou/QCNet
# Reproduces the pins from environment.yml via pip (conda's exact build-hash env
# failed to resolve reliably; README explicitly allows "install latest PyTorch/PyG/Lightning").
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n qcnet python=3.8.16 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "qcnet", "/bin/bash", "-c"]

# torch2.0.1 / cu11.8, matching environment.yml's pytorch=2.0.1=...cuda11.8...
RUN pip install --no-cache-dir \
    torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# PyG core + scatter/sparse/cluster wheels matching torch-2.0.0+cu118 (env.yml: pyg=2.3.0)
RUN pip install --no-cache-dir torch_geometric==2.3.0 \
    && pip install --no-cache-dir torch_scatter==2.1.1 torch_sparse==0.6.17 torch_cluster==1.6.1 \
       -f https://data.pyg.org/whl/torch-2.0.0+cu118.html

RUN pip install --no-cache-dir \
    pytorch-lightning==2.0.4 \
    torchmetrics==0.11.4 \
    numpy==1.24.3 \
    pandas \
    tqdm \
    av2

RUN echo "conda activate qcnet" >> /root/.bashrc
ENV PATH=/opt/conda/envs/qcnet/bin:$PATH

WORKDIR /workspace
CMD ["/bin/bash"]
