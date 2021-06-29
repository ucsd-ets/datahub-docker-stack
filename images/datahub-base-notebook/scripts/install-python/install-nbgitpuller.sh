#!/bin/sh -x
pip install git+https://github.com/data-8/gitautosync &&
  jupyter serverextension enable --py nbgitpuller --sys-prefix
