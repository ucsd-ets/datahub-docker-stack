#!/bin/sh -x

# Add kernelspec
ipython kernel install --name "python3_clean" \
                       --display-name "Python 3 (clean)" \
                       --sys-prefix

# Add to kernel config (set ENV PYTHONNOUSERSITE to 1)
output=$(jq -s add /opt/conda/share/jupyter/kernels/python3_clean/kernel.json /usr/share/datahub/scripts/install-python/kernel_env.json)
echo "$output" > /opt/conda/share/jupyter/kernels/python3_clean/kernel.json
