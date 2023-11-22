ARG BASE_TAG=latest
FROM ghcr.io/ucsd-ets/datascience-notebook:2023.4-fix-rstudio-proxy

USER root

# tensorflow, pytorch stable versions
# https://pytorch.org/get-started/previous-versions/
# https://www.tensorflow.org/install/source#linux

# coerce rebuild in only this nteb

ARG LIBNVINFER=7.2.2 LIBNVINFER_MAJOR_VERSION=7 CUDA_VERSION=12.2

RUN apt-get update && \
  apt-get install -y \
  libtinfo5 build-essential && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Symbolic link for Stata 17 dependency on libncurses5
RUN ln -s libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5

COPY run_jupyter.sh /
RUN chmod +x /run_jupyter.sh

# TODO: Investigate which of these are needed
COPY cudatoolkit_env_vars.sh cudnn_env_vars.sh tensorrt_env_vars.sh /etc/datahub-profile.d/
COPY activate.sh /tmp/activate.sh
COPY workflow_tests /opt/workflow_tests
ADD manual_tests /opt/manual_tests

RUN chmod 777 /etc/datahub-profile.d/*.sh /tmp/activate.sh

RUN apt update && apt install -y wget && \
    wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/libcudnn8_8.9.6.50-1+cuda12.2_amd64.deb && \
    dpkg -i libcudnn8_8.9.6.50-1+cuda12.2_amd64.deb && \
    rm libcudnn8_8.9.6.50-1+cuda12.2_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER jovyan

# CUDA 12
# tf requirements: https://www.tensorflow.org/install/pip#linux
RUN mamba install -c "nvidia/label/cuda-12.2" cuda-nvcc -y && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
 mamba clean -a -y

#RUN mamba list | egrep '(cuda-version|nvidia/label/cuda)' | awk '{ print $1"=="$2;}' > public/envs/test3/conda-meta/pinned

RUN mamba install nccl -c conda-forge -y && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y

# install protobuf to avoid weird base type error. seems like if we don't then it'll be installed twice.
# https://github.com/spesmilo/electrum/issues/7825
# pip cache purge didnt work here for some reason.
#RUN mamba install protobuf=3.20.3
RUN pip install --no-cache-dir protobuf==3.20.3

# Currently, opencv+tensorflow* are problematic with mamba...

# cuda-python installed to have parity with tensorflow and cudnn
# Install pillow<7 due to dependency issue https://github.com/pytorch/vision/issues/1712
# tensorrt installed to fix not having libnvinfer that has caused tensorflow issues.
RUN pip install opencv-contrib-python-headless \
    opencv-python \
    datascience \
    nvidia-cudnn-cu12==8.9.6.50 \
    tensorflow==2.14.0 \ 
    tensorflow-datasets \
    tensorrt==8.6.1 && \
    fix-permissions $CONDA_DIR && \ 
    fix-permissions /home/$NB_USER && \
    pip cache purge

# ntlk_data cannot currently be installed with mamba (while we have python 3.8).
# datascience cannot be installed with mamba
# The latest version of pytables, a dependency, only supports python 3.9 and up.
# The latest compatible version (3.6.1) seems to be broken.
# pytables is necessary, otherwise nltk will install out-of-date package
# pytables on conda == tables on pip (???)
# without pytables explicitly defined, version 3.6 will be installed (which seems to be broken when testing the import)

RUN mamba install pyqt \
  # datascience \
  scapy \
  nltk_data \
  #opencv \
  pycocotools \
  pillow \
  #tensorflow=2.13.1 \
  #tensorflow-datasets \
  keras=2.13.1 \
  -c conda-forge && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y

    # no purge required but no-cache-dir is used. pip purge will actually break the build here!

# torch must be installed separately since it requires a non-pypi repo. See stable version above
#RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/${TORCH_VIS_VER}


# We already have the lib files imported into LD_LIBRARY_PATH by CUDDN and the cudatoolkit. let's remove these and save some image space.
# Beware of potentially needing to update these if we update the drivers.
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER && \
  mamba clean -a -y && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_cnn_infer.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcublasLt.so.11 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_adv_infer.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_adv_train.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_cnn_train.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_ops_infer.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcudnn_ops_train.so.8 && \
  rm /opt/conda/lib/python3.9/site-packages/torch/lib/libcublas.so.11

USER $NB_UID:$NB_GID
ENV PATH=${PATH}:/usr/local/nvidia/bin:/opt/conda/bin

#ENV CUDNN_PATH=/opt/conda/lib/python3.9/site-packages/nvidia/cudnn

# starts like this: /opt/conda/pkgs/cudnn-8.6.0.163-pypi_0 8.8.1.3-pypi_0/lib/:/opt/conda/pkgs/cudatoolkit-11.8.0-h37601d7_11/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
# need to have the end result of running 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/conda/lib/python3.9/site-packages/nvidia/cudnn/lib'
# then the gpu can be detected via CLI.
#ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/conda/lib/python3.9/site-packages/nvidia/cudnn/lib

# Do some CONDA/CUDA stuff
# Copy libdevice file to the required path
#RUN mkdir -p $CONDA_DIR/lib/nvvm/libdevice && \
#  cp $CONDA_DIR/lib/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/

RUN . /tmp/activate.sh
