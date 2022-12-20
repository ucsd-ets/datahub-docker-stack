ARG BASE_TAG=latest
FROM ucsdets/datahub-base-notebook:$BASE_TAG

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

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
RUN conda install \
	cudatoolkit=11.7 \
	cudnn=8.2.1 \
	nccl \
	-y && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER

# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
RUN pip install --no-cache-dir  datascience \
	PyQt5 \
	scapy \
	nltk \
	opencv-contrib-python-headless \
	opencv-python \
	pycocotools \
	pillow \
	tensorflow-gpu==2.6 && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER

# Update these in spec.yml according to https://pytorch.org/get-started/locally/
RUN mamba install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia

RUN ln -s /usr/local/nvidia/bin/nvidia-smi /opt/conda/bin/nvidia-smi

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin

RUN for script in /etc/datahub-profile.d/*.sh; do . "$script"; done
