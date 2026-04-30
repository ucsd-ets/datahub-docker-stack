ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

# Python/Mamba deps
## Package versions
## tf 2.13 does not work with torch 2.2.1. Both require conflicting versions of typing-extensions
## CUDA 11: ARG CUDA_VERSION=11.8 CUDNN_VERSION=8.7.0.84 \

## keras 3>= doesn't work with transformers as of 3-5-25. Check this when building future stable images.
ARG CUDA_VERSION=12.6 CUDNN_VERSION=9.5.1.17 LIBNVINFER=7.2.2 LIBNVINFER_MAJOR_VERSION=7 \
   TENSORRT_VERSION=10.7.0 TORCH_VERSION=2.6.0


# apt deps
RUN apt-get update && \
  apt-get install -y \
  libtinfo5 build-essential && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
## Symbolic link for Stata 17 dependency on libncurses5
RUN ln -s libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5

# Jupyter setup
COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

# Scripts setup
COPY cudatoolkit_env_vars.sh cudnn_env_vars.sh tensorrt_env_vars.sh /etc/datahub-profile.d/
COPY activate.sh /tmp/activate.sh

# Add tests
RUN mkdir -p /opt/workflow_tests
COPY workflow_tests/* /opt/workflow_tests/
ADD manual_tests /opt/manual_tests

RUN chmod 777 /etc/datahub-profile.d/*.sh /tmp/activate.sh

# cudnn (TBD)
#RUN apt update && apt install -y wget && \
#    wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/libcudnn8_8.9.6.50-1+cuda11.8_amd64.deb && \
#    dpkg -i libcudnn8_8.9.6.50-1+cuda11.8_amd64.deb && \
#    rm libcudnn8_8.9.6.50-1+cuda11.8_amd64.deb && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

USER jovyan

RUN pip3 install --no-cache-dir --upgrade uv

RUN uv pip install --system \
        --extra-index-url https://pypi.nvidia.com \
        --extra-index-url https://download.pytorch.org/whl/cu128 \
        nvidia-cuda-nvcc-cu12 \
        nvidia-nccl-cu12 \
        cuda-python \
        opencv-contrib-python-headless \
        opencv-python \
        PyQt5 \
        pycocotools \
        pillow \
        scapy \
        nvidia-cudnn-cu12 \
        torch==$TORCH_VERSION \
        torchvision \
        torchaudio \
        tensorrt \
        transformers \
        datasets \
        accelerate \
        huggingface-hub \
        timm \
    && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    uv cache clean

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

# Run datahub scripts
RUN . /tmp/activate.sh
