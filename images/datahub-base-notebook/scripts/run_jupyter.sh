#!/usr/bin/env bash

export PATH=$PATH:/usr/local/nvidia/bin

jupyter notebook "$@"
