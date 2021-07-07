#!/bin/bash

set -x -e -o pipefail

for f in /usr/share/datahub/scripts/install-python/*.sh; do
  bash "$f" -H || break
done