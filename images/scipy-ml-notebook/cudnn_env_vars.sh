#!/bin/bash

# set systemwide env variables for Conda package: cudnn
cudnn_version=$(conda list 2> /dev/null | grep cudnn | awk -F' ' '{ print $2 "-" $3 }')

export LD_LIBRARY_PATH=/opt/conda/pkgs/cudnn-$cudnn_version/lib/:${LD_LIBRARY_PATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/conda/lib/python3.9/site-packages/nvidia/cudnn/lib
