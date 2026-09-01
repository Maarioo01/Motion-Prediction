# TrajFlow (top 5-6, flow-matching prediction on Waymo, IROS'25)
# https://github.com/DSL-Lab/TrajFlow
#
# NOTE: this repo compiles custom CUDA ops (MTR-style knn/attention kernels) against
# the *source tree*, and we mount that source from the host at runtime (not baked into
# the image) so it stays live-editable. So the extension build itself happens in
# entrypoint.sh at container start, not here at image-build time - this stage only
# prepares the conda env + toolchain (incl. nvcc via conda, since the base image has none).
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n trajflow python=3.10 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "trajflow", "/bin/bash", "-c"]

# Python 3.10 is required specifically for this TF package (per README)
RUN pip install --no-cache-dir waymo-open-dataset-tf-2-12-0

COPY setup/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# torch/torchvision/torchaudio installed LAST and re-pinned: waymo-open-dataset-tf's TF
# ecosystem and/or the unpinned "torch" requires of accelerate/ema-pytorch in
# requirements.txt cause pip's resolver to silently swap our pinned +cu118 build for a
# plain PyPI (cu121-bundled) torch if installed earlier - verified via `pip check`
# reporting torchvision/torchaudio needing torch==2.2.0 but a bare 2.1.2 being installed.
RUN pip install --no-cache-dir \
    torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 \
    --index-url https://download.pytorch.org/whl/cu118

# nvcc matching the cu118 torch build, installed into the conda env (no system CUDA needed).
# CUDA 11.8's nvcc refuses any host gcc newer than 11 ("gcc versions later than 11 are
# not supported"), but the miniconda3 base image's apt gcc is newer - install gcc 11 via
# conda-forge so it takes priority in PATH ahead of the system compiler.
RUN conda install -y -c "nvidia/label/cuda-11.8.0" cuda-toolkit=11.8 \
    && conda install -y -c conda-forge ninja git gcc=11 gxx=11 \
    && conda clean -afy

ENV TORCH_CUDA_ARCH_LIST="8.6"
ENV PATH=/opt/conda/envs/trajflow/bin:$PATH
RUN echo "conda activate trajflow" >> /root/.bashrc

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
