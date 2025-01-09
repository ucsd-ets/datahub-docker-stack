ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

# Python/Mamba deps
ARG CUDA_VERSION=12.1 \
  TENSORFLOW_VERSION=2.17.0 KERAS_VERSION=3.5.0 TENSORRT_VERSION=8.6.1 TORCH_VERSION=2.3.1

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
RUN mamba install -c rapidsai-nightly -c conda-forge jupyterlab-nvdashboard

# CUDA setup w/mamba
RUN mamba install -c "nvidia/label/cuda-12.1.1" \
    cuda-nvcc \
    cuda-version=$CUDA_VERSION \
    cuda-toolkit=$CUDA_VERSION \
    nccl \
    cudnn \
    libcublas \
    -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Install scipy pip packages
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
RUN pip install torch==$TORCH_VERSION torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir && \
  pip install tensorflow==$TENSORFLOW_VERSION tensorflow-datasets tensorrt==$TENSORRT_VERSION keras==$KERAS_VERSION tf-keras==$TENSORFLOW_VERSION --no-cache-dir && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y && \
  pip cache purge

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

# TensorRT fix for tensorflow
## https://github.com/tensorflow/tensorflow/issues/61468 (could not find TensorRT)
## To be removed with TF 2.18+
RUN ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.$TENSORRT_VERSION && \
    ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.$TENSORRT_VERSION

# Run datahub scripts
RUN . /tmp/activate.sh
