#!/bin/bash

# set systemwide env variables for Conda package: cudnn
#CUDA 11:
#cudatoolkit=$(ls /opt/conda/pkgs | grep cudatoolkit | head -1 | cut -d '-' -f 2-)

#export LD_LIBRARY_PATH=/opt/conda/pkgs/cudatoolkit-$cudatoolkit/lib:${LD_LIBRARY_PATH}

# pathing for ptxas/libdevice. see https://www.tensorflow.org/install/pip#linux
export XLA_FLAGS=--xla_gpu_cuda_data_dir=$CONDA_DIR/lib/

