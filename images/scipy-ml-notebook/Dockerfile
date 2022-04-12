ARG BASE_TAG=latest
FROM ucsdets/datahub-base-notebook:$BASE_TAG

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

RUN apt-get update && \
	apt-get install -y \
	libtinfo5 && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

USER jovyan

# CUDA 11
RUN conda install \
	cudatoolkit=11.2 \
	cudnn \
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
	jupyter-tensorboard \
	opencv-python \
	pycocotools \
	pillow \
	tensorflow-gpu==2.6 && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER

# Update these in spec.yml according to https://pytorch.org/get-started/locally/
ARG TORCH_VER="1.7.1+cu101"
ARG TORCH_VIS_VER="0.8.2+cu101"
ARG TORCH_AUD_VER="0.7.2"

# torch must be installed separately since it requires a non-pypi repo. See stable version above
RUN pip install torch==${TORCH_VER} torchvision==${TORCH_VIS_VER} torchaudio==${TORCH_AUD_VER} \
	-f https://download.pytorch.org/whl/torch_stable.html && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER


RUN ln -s /usr/local/nvidia/bin/nvidia-smi /opt/conda/bin/nvidia-smi && \
    ln -s /usr/lib/libncursesw.so.6.0 /usr/lib/libncurses.so.5 && \
    ln -s /usr/lib/libncursesw.so.6.0 /usr/lib/libtinfo.so.5


USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin
ENV LD_LIBRARY_PATH=/opt/conda/pkgs/cudatoolkit-11.2.2-he111cf0_8/lib/:${LD_LIBRARY_PATH}
RUN echo 'here'
