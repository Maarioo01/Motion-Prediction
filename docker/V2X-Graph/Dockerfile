# V2X-Graph (NeurIPS 2024) - https://github.com/AIR-THU/V2X-Graph
# Cooperative trajectory forecasting on V2X-Seq-TFD and V2X-Traj; Phase 0 checklist B2.
#
# Python 3.10, not the README's 3.8: requirements.txt pins scipy==1.15.3 and
# Shapely==2.1.0, which only exist for Python >= 3.10. torch 1.12.1+cu116 runs on the
# 3090 (sm_86) but not on a 5090 (sm_120 needs CUDA >= 12.8) - see BUILD_GOTCHAS.md.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git git-lfs wget libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n v2xgraph python=3.10 && conda clean -afy
SHELL ["conda", "run", "--no-capture-output", "-n", "v2xgraph", "/bin/bash", "-c"]

# Exact local-version torch first, then everything else under a constraint so nothing
# can swap it for a default-PyPI build (BUILD_GOTCHAS: "pin the explicit local version").
RUN pip install --no-cache-dir torch==1.12.1+cu116 \
    --extra-index-url https://download.pytorch.org/whl/cu116 \
    && echo "torch==1.12.1+cu116" > /tmp/constraints.txt

COPY requirements.txt /tmp/requirements.txt
# setuptools pin: pytorch_lightning 1.5 imports pkg_resources (removed in setuptools>=81).
RUN grep -v '^torch==' /tmp/requirements.txt > /tmp/req-notorch.txt \
    && pip install --no-cache-dir -c /tmp/constraints.txt \
       --extra-index-url https://download.pytorch.org/whl/cu116 \
       -r /tmp/req-notorch.txt matplotlib setuptools==69.5.1

# Argoverse 1 API, needed only for its map utilities (DAIR-V2X-Seq's dair_map_api).
# Its install_requires pins 2021-era numpy==1.19 / sklearn / hydra 1.1, none of which the
# map code path uses -> --no-deps, pinned commit (master HEAD, 2022-08-08), plus the four
# extra packages its import chain (argoverse.utils.__init__ -> mpl_plotting_utils, ...)
# actually needs, found by importing every V2X-Graph entry point.
RUN pip install --no-cache-dir --no-deps \
    git+https://github.com/argoverse/argoverse-api.git@f886ac54fba9f06f8a7d109eb663c7f501b3aa8e \
    && pip install --no-cache-dir -c /tmp/constraints.txt \
       descartes==1.1.0 imageio==2.38.0 omegaconf==2.4.0 colour==0.1.5

RUN pip check || true
RUN python -c "import torch; assert torch.__version__ == '1.12.1+cu116', torch.__version__"

# DAIR-V2X-Seq's dataset API (dair_map_api) is mounted at /deps/DAIR-V2X-Seq.
ENV PYTHONPATH=/deps/DAIR-V2X-Seq/projects/dataset
RUN echo "conda activate v2xgraph" >> /root/.bashrc
ENV PATH=/opt/conda/envs/v2xgraph/bin:$PATH

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
