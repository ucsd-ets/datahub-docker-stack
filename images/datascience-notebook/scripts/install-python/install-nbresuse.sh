#!/bin/sh -x

pip install --no-cache-dir git+https://github.com/jupyter-server/jupyter-resource-usage
#pip install --no-cache-dir git+https://github.com/ucsd-ets/nbresuse.git 
    # nbclassic
    #&& \ jupyter server extension enable --sys-prefix --py nbresuse && \
	#jupyter lab extension enable --sys-prefix --py nbresuse
