#!/bin/bash

for script in /etc/datahub-profile.d/*.sh; do
    . "$script"
done