#!/bin/bash

# Put the CUDA libraries from the nvidia-*-cu12 wheels on LD_LIBRARY_PATH.
# TensorFlow dlopens libcudart/libcublas/libcudnn/libcufft/... by soname and only
# carries an RPATH for cusolver, so without these dirs on the loader path it
# reports no GPU ("Cannot dlopen some GPU libraries") while torch, which resolves
# its own copies via RPATH, still sees the card. This used to cover cudnn only.
# The image also registers the same dirs with ldconfig at build time, which is
# what covers non-login shells such as `launch.sh -f pytest /opt/workflow_tests`.
NVIDIA_LIB_DIRS=$(python -c "import glob, os, site; \
print(':'.join(sorted(d for sp in site.getsitepackages() \
                      for d in glob.glob(os.path.join(sp, 'nvidia', '*', 'lib')))))" 2>/dev/null)

if [ -n "$NVIDIA_LIB_DIRS" ]; then
    export LD_LIBRARY_PATH="${NVIDIA_LIB_DIRS}:${LD_LIBRARY_PATH}"
fi
