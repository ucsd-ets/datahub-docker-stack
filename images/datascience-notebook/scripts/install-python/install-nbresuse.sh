#!/bin/sh -x
pip install --no-cache-dir git+https://github.com/ucsd-ets/nbresuse.git && \
	jupyter serverextension enable --sys-prefix --py nbresuse && \
	jupyter nbextension install --sys-prefix --py nbresuse && \
	jupyter nbextension enable --sys-prefix --py nbresuse
