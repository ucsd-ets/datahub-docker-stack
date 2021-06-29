#!/bin/sh -x

# Add kernelspec
ipython kernel install --name "python3_clean" \
                       --display-name "Python 3 (clean)" \
                       --sys-prefix

# Add to kernel config (set ENV PYTHONNOUSERSITE to 1)
sed -i "s~\"python\"$~\"python\",\n \"env\": {\n  \"PYTHONNOUSERSITE\": \"1\"\n }~" \
       /opt/conda/share/jupyter/kernels/python3_clean/kernel.json