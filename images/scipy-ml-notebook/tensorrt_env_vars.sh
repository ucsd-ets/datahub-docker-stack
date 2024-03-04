#!/bin/bash

# put tensorrt lib into LD_LIBRARY_PATH
#export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt:$LD_LIBRARY_PATH"

# tensorrt 8.6+?
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt_bindings:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt_libs:$LD_LIBRARY_PATH"
