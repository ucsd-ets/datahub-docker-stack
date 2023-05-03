#!/bin/sh -x

git clone https://github.com/ucsd-ets/local-env-backup.git /tmp/local-env-backup

pip install --no-cache-dir /tmp/local-env-backup

rm -rf /tmp/local-env-backup