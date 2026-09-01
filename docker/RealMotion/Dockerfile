# RealMotion (top 4, "Motion Forecasting in Continuous Driving", NeurIPS 2024)
# https://github.com/fudan-zvg/RealMotion
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n realmotion python=3.10 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "realmotion", "/bin/bash", "-c"]

RUN pip install --no-cache-dir \
    torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# NATTEN prebuilt wheel matched to torch 2.0.0 + cu118 (per README) is no longer served:
# shi-labs.com's cert is expired, and its successor whl.natten.org dropped torch200 builds
# (oldest available there is torch250). Build NATTEN 0.17.3 from source against our exact
# torch 2.0.1+cu118 instead, which needs nvcc in the env.
# CUDA 11.8's nvcc refuses any host gcc newer than 11, but the base image's apt gcc is
# newer - install gcc 11 via conda-forge so it takes priority in PATH. This is very
# likely also why natten silently fell back to a CPU-only build the first time around
# (its setup.py probably swallows the nvcc failure rather than surfacing it).
RUN conda install -y -c "nvidia/label/cuda-11.8.0" cuda-toolkit=11.8 \
    && conda install -y -c conda-forge ninja gcc=11 gxx=11 \
    && conda clean -afy
ENV TORCH_CUDA_ARCH_LIST="8.6"
# setuptools>=81 dropped the bundled pkg_resources module, but torch 2.0.1's
# cpp_extension.py (used by natten's build) still does `from pkg_resources import
# packaging` - pin to a pre-removal setuptools for the build.
RUN pip install --no-cache-dir ninja packaging wheel "setuptools==69.5.1"
# `docker build` has no GPU attached. NATTEN's setup.py gates its CUDA build on
# `HAS_CUDA = FORCE_CUDA or (torch.cuda.is_available() and CUDA_HOME)` - since
# torch.cuda.is_available() is False at build time, NATTEN_CUDA_ARCH alone (which only
# supplies the target architecture) was NOT enough and it silently built CPU-only;
# FORCE_CUDA=1 is what actually flips HAS_CUDA to true.
ENV FORCE_CUDA="1"
ENV NATTEN_CUDA_ARCH="8.6"
RUN pip install --no-cache-dir --no-build-isolation natten==0.17.3

RUN echo "conda activate realmotion" >> /root/.bashrc
ENV PATH=/opt/conda/envs/realmotion/bin:$PATH

WORKDIR /workspace
CMD ["/bin/bash"]
