ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:${BASE_TAG}

USER root

# Package versions (adjust as needed)
ARG CUDA_VERSION=12.1
ARG CUDNN_VERSION=8.9.7.29
ARG TENSORFLOW_VERSION=2.17.0
ARG KERAS_VERSION=3.5.0
ARG TENSORRT_VERSION=8.6.1
ARG TORCH_VERSION=2.3.1
ARG PROTOBUF_VERSION=3.20.3

# apt deps
RUN apt-get update && \
  apt-get install -y libtinfo5 build-essential && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Symbolic link for Stata 17 dependency on libncurses5
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

# Switch to non-root user for installing packages via mamba/pip
USER jovyan

# Install nvdashboard for GPU monitoring
RUN mamba install -c rapidsai-nightly -c conda-forge jupyterlab-nvdashboard && \
    mamba clean -a -y

# Install CUDA toolkit, NCCL, cuDNN via Conda
RUN mamba install -c "nvidia/label/cuda-12.1.1" \
    cuda-nvcc \
    cuda-toolkit=${CUDA_VERSION} \
    cuda-version=${CUDA_VERSION} \
    nccl \
    cudnn=${CUDNN_VERSION} \
    -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Install protobuf via pip to ensure a specific version
RUN pip install --no-cache-dir protobuf==${PROTOBUF_VERSION}

# Install other Python packages that are simpler via pip
RUN pip install --no-cache-dir opencv-contrib-python-headless opencv-python && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    pip cache purge

# Install common packages via conda-forge
RUN mamba install -c conda-forge pyqt pycocotools pillow scapy && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean --all

# Install PyTorch and GPU support from Conda
# Use pytorch & nvidia channels to ensure proper CUDA integration
RUN mamba install pytorch==${TORCH_VERSION} torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Install TensorFlow, Keras, and TF datasets from conda-forge if available
# Note: Check if these versions are available and GPU-accelerated on conda-forge.
RUN mamba install tensorflow==${TENSORFLOW_VERSION} keras==${KERAS_VERSION} tensorflow-datasets -c conda-forge -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y

# Additional ML packages via pip
RUN pip install --no-cache-dir transformers datasets accelerate huggingface-hub timm && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    mamba clean -a -y && \
    pip cache purge

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

# CUDA fixes for CONDA
RUN mkdir -p $CONDA_DIR/lib/nvvm/libdevice && \
    cp $CONDA_DIR/nvvm/libdevice/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/

# TensorRT fix for TensorFlow (if needed)
# Adjust paths as necessary, depending on how tensorrt is installed.
#RUN ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.${TENSORRT_VERSION} && \
#    ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.${TENSORRT_VERSION}

# Run datahub scripts
RUN . /tmp/activate.sh