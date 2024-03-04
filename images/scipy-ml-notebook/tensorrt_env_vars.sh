#!/bin/bash

# put tensorrt lib into LD_LIBRARY_PATH
#export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt:$LD_LIBRARY_PATH"

# https://github.com/tensorflow/tensorflow/issues/61468 (could not find TensorRT)
# This will most definitely have to be changed after 8.6.1...
ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer_plugin.so.8.6.1
ln -s /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.8 /opt/conda/lib/python3.11/site-packages/tensorrt_libs/libnvinfer.so.8.6.1

# tensorrt 8.6+
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt_bindings:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/tensorrt_libs:$LD_LIBRARY_PATH"