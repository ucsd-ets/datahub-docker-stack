ARG BASE_TAG=2025.4-py312-cuda124-exp
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

# Python/Mamba deps
## tf 2.18+ does not work with cu124 pytorch. tf 2.18 needs cudnn 9.3+, torch installs cudnn 9.1
ARG CUDA_VERSION=12.4 \
  TENSORFLOW_VERSION=2.17.0 KERAS_VERSION=3.7.0 TENSORRT_VERSION=10.7.0 TORCH_VERSION=2.5.1

# apt deps
RUN apt-get update && \
  apt-get install -y \
  libtinfo6 build-essential && \
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

USER jovyan

# Install nvdashboard for GPU monitoring
RUN mamba install -c rapidsai-nightly -c conda-forge jupyterlab-nvdashboard \
    -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# CUDA setup w/mamba
# cuda-toolkit is a skeleton package on CUDA 12, unlike CUDA <= 11
RUN mamba install -c "nvidia/label/cuda-${CUDA_VERSION}" \
    -c conda-forge \
    cuda-nvcc \
    cuda-version=${CUDA_VERSION} \
    -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Install scipy pip packages
## cuda-python installed to have parity with tensorflow and cudnn
## Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
## tensorrt installed to fix not having libnvinfer that has caused tensorflow issues.
RUN pip install opencv-contrib-python-headless \
    opencv-python && \
    fix-permissions $CONDA_DIR && \ 
    fix-permissions /home/$NB_USER && \
    pip cache purge

RUN mamba install -c conda-forge pyqt pycocotools pillow scapy && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean --all

# Install CUDA/Torch/Tensorflow/Keras w/pip
# TF Compatibility Matrix: https://www.tensorflow.org/install/source?hl=en#gpu
## no purge required but no-cache-dir is used. pip purge will actually break the build here!
## Beware of potentially needing to update these if we update the drivers.
## Check tensorrt_env_vars.sh if you have to bump tensorrt!
## We install torch and its dependencies EXCLUDING any nvidia* deps. These are handled by our conda env.
RUN pip install --no-cache-dir \
    torch==${TORCH_VERSION} \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu124 && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

RUN pip install --no-cache-dir \
    tensorflow==$TENSORFLOW_VERSION tensorflow-datasets tensorrt==$TENSORRT_VERSION keras==$KERAS_VERSION tf-keras==$TENSORFLOW_VERSION && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

RUN pip install transformers datasets accelerate huggingface-hub timm && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y && \
    pip cache purge

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

# CUDA fixes for CONDA
## Copy libdevice file to the required path
RUN mkdir -p $CONDA_DIR/lib/nvvm/libdevice && \
    cp $CONDA_DIR/nvvm/libdevice/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/
    #CUDA 11: cp $CONDA_DIR/lib/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/

# Run datahub scripts
RUN . /tmp/activate.sh