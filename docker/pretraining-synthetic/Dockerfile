# Pretraining on Synthetic Driving Data for Trajectory Prediction (top 12, IROS 2024)
# https://github.com/yhli123/Pretraining_on_Synthetic_Driving_Data_for_Trajectory_Prediction
# A DenseTNT variant; setup follows DenseTNT's own README (this repo has no env spec of
# its own) plus the Argoverse 1 API. Cython extension (src/utils_cython.pyx) is compiled
# against the host-mounted source at container start (see entrypoint.sh), same reasoning
# as TrajFlow's CUDA ops - keeps /workspace live-editable rather than baked into the image.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n pretrainsynth python=3.8 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "pretrainsynth", "/bin/bash", "-c"]

# Argoverse 1 API (github-only, no PyPI package) - installed from a pinned clone.
# Its own install_requires exact-pins ancient releases (numpy==1.19, hydra-core==1.1.0,
# omegaconf==2.1.0) that no longer resolve; none of them are actually imported by the
# two entry points this repo uses (ArgoverseMap, eval_forecasting - verified their
# import graphs directly), which only need numpy/matplotlib/shapely/opencv. Install
# with --no-deps and supply modern versions of just those instead.
RUN git clone --depth 1 https://github.com/argoverse/argoverse-api.git /opt/argoverse-api \
    && pip install --no-cache-dir --no-deps /opt/argoverse-api \
    && pip install --no-cache-dir numpy matplotlib shapely opencv-python-headless pandas scipy \
       typing_extensions colour descartes h5py imageio numba pillow scikit-learn \
       omegaconf hydra-core

# DenseTNT's own (minimal, unpinned) requirements, minus torch which is pinned separately.
RUN pip install --no-cache-dir cython tqdm matplotlib scipy

# Pinned torch, installed last per the torch-gets-silently-swapped lesson learned on the
# other repos in this project.
RUN pip install --no-cache-dir \
    torch==2.0.1 torchvision==0.15.2 \
    --index-url https://download.pytorch.org/whl/cu118

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN echo "conda activate pretrainsynth" >> /root/.bashrc
ENV PATH=/opt/conda/envs/pretrainsynth/bin:$PATH

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
