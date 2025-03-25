#!/usr/bin/env bash

cd "$(dirname "$0")"

docker run \
       --rm \
       --volume $PWD:/root/openplc  \
       --interactive \
       --tty \
       halucinator_openplc_dev \
       /bin/sh -c 'cd /root/openplc; exec tmux'
