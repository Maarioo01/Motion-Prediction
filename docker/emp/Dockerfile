# emp / Efficient Motion Prediction (top 8, IROS 2024) - https://github.com/a-pru/emp
# No custom CUDA extensions - pure pip env.
FROM continuumio/miniconda3:24.9.2-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -y -n emp python=3.8.18 && conda clean -afy

SHELL ["conda", "run", "--no-capture-output", "-n", "emp", "/bin/bash", "-c"]

# requirements.txt bumped pytorch-lightning 1.8.2 -> 1.8.6 (still 1.8.x): the 1.8.2
# wheel on PyPI has malformed metadata ("torch (>=1.9.*)", an invalid PEP 440
# specifier) that pip >=24.1 refuses to parse at all. Also dropped onnx/onnxscript/
# onnxruntime, which only the optional onnx/export_onnx.py script uses (not the core
# train.py/eval.py path) and whose pinned versions have no mutually-compatible set.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir av2

# README tested both torch 1.11.0+cu113 and 2.1.1+cu121; using the newer combo. Installed
# last (pinned, after requirements.txt) per the torch-gets-silently-swapped lesson.
RUN pip install --no-cache-dir \
    torch==2.1.1 torchvision==0.16.1 \
    --index-url https://download.pytorch.org/whl/cu121

RUN echo "conda activate emp" >> /root/.bashrc
ENV PATH=/opt/conda/envs/emp/bin:$PATH

WORKDIR /workspace
CMD ["/bin/bash"]
