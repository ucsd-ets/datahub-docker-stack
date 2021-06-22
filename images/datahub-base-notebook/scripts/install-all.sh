#!/bin/bash


for f in /usr/share/datahub/scripts/install/*.sh; do
  bash "$f" -H || break
done