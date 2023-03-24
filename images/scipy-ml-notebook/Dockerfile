ARG BASE_TAG=latest
FROM ucsdets/datahub-base-notebook:$BASE_TAG

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

ARG LIBNVINFER=7.2.2 LIBNVINFER_MAJOR_VERSION=7 CUDA_VERSION=11.2

RUN apt-get update && \
	apt-get install -y \
	libtinfo5 build-essential && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# Symbolic link for Stata 17 dependency on libncurses5
RUN ln -s libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5

COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

COPY cudatoolkit_env_vars.sh /etc/datahub-profile.d/cudatoolkit_env_vars.sh
COPY cudnn_env_vars.sh /etc/datahub-profile.d/cudnn_env_vars.sh
COPY activate.sh /tmp/activate.sh

RUN chmod 777 /etc/datahub-profile.d/*.sh /tmp/activate.sh

USER jovyan

# CUDA 11
# tf requirements: https://www.tensorflow.org/install/pip#linux
RUN mamba install \
	cudatoolkit=11.2 \
	cudnn=8.1.0 \
	nccl \
	-y && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER

RUN apt-get install -y \
  libnvinfer${LIBNVINFER_MAJOR_VERSION}=${LIBNVINFER}-1+${CUDA_VERSION} \
  libnvinfer-plugin${LIBNVINFER_MAJOR_VERSION}=${LIBNVINFER}-1+${CUDA_VERSION}

# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
RUN pip install --no-cache-dir  datascience \
	PyQt5 \
	scapy \
	nltk \
	opencv-contrib-python-headless \
	opencv-python \
	pycocotools \
	pillow \
	tensorflow==2.10.0 && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER

# Update these in spec.yml according to https://pytorch.org/get-started/locally/
ARG TORCH_VER="1.7.1+cu101"
ARG TORCH_VIS_VER="0.8.2+cu101"
ARG TORCH_AUD_VER="0.7.2"

# torch must be installed separately since it requires a non-pypi repo. See stable version above
RUN pip install torch==${TORCH_VER} torchvision==${TORCH_VIS_VER} torchaudio==${TORCH_AUD_VER} \
	-f https://download.pytorch.org/whl/torch_stable.html

# to use nvidia-smi command to check GPU & driver
# RUN ln -s /usr/local/nvidia/bin/nvidia-smi /opt/conda/bin/nvidia-smi
#RUN . /tmp/activate.sh && echo "Activate ran successfully"
#
USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

RUN . /tmp/activate.sh

