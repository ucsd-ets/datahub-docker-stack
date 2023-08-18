ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:$BASE_TAG

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

# coerce rebuild in only this nteb

ARG LIBNVINFER=7.2.2 LIBNVINFER_MAJOR_VERSION=7 CUDA_VERSION=11.8

RUN apt-get update && \
	apt-get install -y \
	libtinfo5 build-essential && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# Symbolic link for Stata 17 dependency on libncurses5
RUN ln -s libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5

COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

COPY cudatoolkit_env_vars.sh cudnn_env_vars.sh tensorrt_env_vars.sh /etc/datahub-profile.d/
COPY activate.sh /tmp/activate.sh
COPY workflow_tests /opt/workflow_tests
ADD manual_tests /opt/manual_tests

RUN chmod 777 /etc/datahub-profile.d/*.sh /tmp/activate.sh

USER jovyan

# CUDA 11 
# tf requirements: https://www.tensorflow.org/install/pip#linux
RUN mamba install \
	cudatoolkit=11.8 \
	nccl \
	-y && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER && \
	mamba clean -a -y

RUN mamba install -c "nvidia/label/cuda-11.8.0" cuda-nvcc -y && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER && \
	mamba clean -a -y

# install protobuf to avoid weird base type error. seems like if we don't then it'll be installed twice.
# https://github.com/spesmilo/electrum/issues/7825
# pip cache purge didnt work here for some reason.
RUN pip install --no-cache-dir protobuf==3.20.3

# cuda-python installed to have parity with tensorflow and cudnn
# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
# tensorrt installed to fix not having libnvinfer that has caused tensorflow issues.
# tensorrt installed to fix not having libnvinfer that has caused tensorflow issues.
RUN pip install --no-cache-dir  datascience \
	PyQt5 \
	scapy \
	nltk \
	opencv-contrib-python-headless \
	opencv-python \
	pycocotools \
	pillow \
	nvidia-cudnn-cu11==8.6.0.163 \
	tensorflow==2.13.* \
	tensorrt \
	keras==2.13.1 && \
	fix-permissions $CONDA_DIR && \
	fix-permissions /home/$NB_USER && \
	pip cache purge

# Update these in spec.yml according to https://pytorch.org/get-started/locally/
ARG TORCH_VER="1.7.1+cu101" \
    TORCH_VIS_VER="0.8.2+cu101" \
    TORCH_AUD_VER="0.7.2"

# torch must be installed separately since it requires a non-pypi repo. See stable version above
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
	pip cache purge

### UNCOMMENT WHEN WE HAVE NVIDIA 11.8 ON NODES
# Update these in spec.yml according to https://pytorch.org/get-started/locally/
#ARG TORCH_VER="cu118"

# torch must be installed separately since it requires a non-pypi repo. See stable version above
#RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/${TORCH_VIS_VER} 

# to use nvidia-smi command to check GPU & driver
# RUN ln -s /usr/local/nvidia/bin/nvidia-smi /opt/conda/bin/nvidia-smi

# RUN . /tmp/activate.sh && echo "Activate ran successfully"


USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

#ENV CUDNN_PATH=/opt/conda/lib/python3.9/site-packages/nvidia/cudnn

# starts like this: /opt/conda/pkgs/cudnn-8.6.0.163-pypi_0 8.8.1.3-pypi_0/lib/:/opt/conda/pkgs/cudatoolkit-11.8.0-h37601d7_11/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
# need to have the end result of running 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/conda/lib/python3.9/site-packages/nvidia/cudnn/lib'
# then the gpu can be detected via CLI.
#ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/conda/lib/python3.9/site-packages/nvidia/cudnn/lib

# Do some CONDA/CUDA stuff
# Copy libdevice file to the required path
RUN mkdir -p $CONDA_DIR/lib/nvvm/libdevice && \
	cp $CONDA_DIR/lib/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/

RUN . /tmp/activate.sh
