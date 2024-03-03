ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:2023.4-scipy-ml-fixup

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

ARG LIBNVINFER=7.2.2 LIBNVINFER_MAJOR_VERSION=7

# Python/Mamba deps
ARG CUDA_VERSION=12.0 CUDNN_VERSION=8.9.2.26 \
  PROTOBUF_VERSION=3.20.3 TENSORFLOW_VERSION=2.15.0 KERAS_VERSION=2.15.0 TENSORRT_VERSION=8.6.1 \
  TORCH_VERSION=2.2.1

# apt deps
RUN apt-get update && \
  apt-get install -y \
  libtinfo5 build-essential && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Symbolic link for Stata 17 dependency on libncurses5
RUN ln -s libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5

# Jupyter setup
COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

# Scripts setup
COPY cudatoolkit_env_vars.sh cudnn_env_vars.sh tensorrt_env_vars.sh /etc/datahub-profile.d/
COPY activate.sh /tmp/activate.sh
COPY workflow_tests /opt/workflow_tests
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

# CUDA 12
# tf requirements: https://www.tensorflow.org/install/pip#linux
RUN mamba install -c "nvidia/label/cuda-12.0.0" cuda-nvcc \
    cuda-toolkit=$CUDA_VERSION \
    nccl \
    -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# install protobuf to avoid weird base type error. seems like if we don't then it'll be installed twice.
# https://github.com/spesmilo/electrum/issues/7825
# pip cache purge didnt work here for some reason.
RUN pip install --no-cache-dir protobuf==$PROTOBUF_VERSION

# cuda-python installed to have parity with tensorflow and cudnn
# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
# tensorrt installed to fix not having libnvinfer that has caused tensorflow issues.
RUN pip install opencv-contrib-python-headless \
    opencv-python && \
    fix-permissions $CONDA_DIR && \ 
    fix-permissions /home/$NB_USER && \
    pip cache purge

RUN mamba install pyqt \
  scapy \
  # datascience \
  pycocotools \
  pillow -y \
  -c conda-forge && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y

# no purge required but no-cache-dir is used. pip purge will actually break the build here!
# We already have the lib files imported into LD_LIBRARY_PATH by CUDDN and the cudatoolkit. let's remove these and save some image space.
# Beware of potentially needing to update these if we update the drivers.
RUN pip install nvidia-cudnn-cu12==$CUDNN_VERSION torch==$TORCH_VERSION torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
  pip install tensorflow==$TENSORFLOW_VERSION tensorflow-datasets tensorrt==$TENSORRT_VERSION keras==$KERAS_VERSION && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y && \
  pip cache purge

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
    cp $CONDA_DIR/nvvm/libdevice/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/

RUN . /tmp/activate.sh
