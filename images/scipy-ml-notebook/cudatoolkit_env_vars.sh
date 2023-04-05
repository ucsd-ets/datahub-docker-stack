#!/bin/bash

# set systemwide env variables for Conda package: cudnn
cudatoolkit=$(conda list 2> /dev/null | grep cudatoolkit | awk -F' ' '{ print $2 "-" $3 }')

export LD_LIBRARY_PATH=/opt/conda/pkgs/cudatoolkit-$cudatoolkit/lib:${LD_LIBRARY_PATH}

mkdir -p $CONDA_DIR/etc/conda/activate.d
printf 'export XLA_FLAGS=--xla_gpu_cuda_data_dir=$CONDA_DIR/lib/\n' >> $CONDA_DIR/etc/conda/activate.d/env_vars.sh
source $CONDA_DIR/etc/conda/activate.d/env_vars.sh
# Copy libdevice file to the required path
mkdir -p $CONDA_DIR/lib/nvvm/libdevice
cp $CONDA_DIR/lib/libdevice.10.bc $CONDA_DIR/lib/nvvm/libdevice/
