#!/bin/bash

# set systemwide env variables for Conda package: cudnn
cudatoolkit=$(conda list 2> /dev/null | grep cudatoolkit | awk -F' ' '{ print $2 "-" $3 }')

export LD_LIBRARY_PATH=/opt/conda/pkgs/cudatoolkit-$cudatoolkit/lib:${LD_LIBRARY_PATH}
