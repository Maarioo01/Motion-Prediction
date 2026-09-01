# GameFormer (top 3, ICCV 2023) - https://github.com/MCZhi/GameFormer
# No custom CUDA extensions - pure pip env. Needs Waymo *scenario* format data (same gap
# as TrajFlow/SceneInformer - see repo README's data-format note).
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n gameformer python=3.8 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "gameformer", "/bin/bash", "-c"]

RUN pip install --no-cache-dir waymo-open-dataset-tf-2-11-0 shapely

# Pinned with the explicit local version (+cu116), not just the bare number - a bare
# pin can silently match an already-installed differently-tagged build pulled in as
# someone else's transitive dependency (see README "Build gotchas").
RUN pip install --no-cache-dir torch==1.12.0+cu116 \
    -f https://download.pytorch.org/whl/torch_stable.html

RUN echo "conda activate gameformer" >> /root/.bashrc
ENV PATH=/opt/conda/envs/gameformer/bin:$PATH

WORKDIR /workspace
CMD ["/bin/bash"]
