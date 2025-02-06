#!/usr/bin/env bash

set -ex

cd "$(dirname "$0")"

docker run \
       --rm \
       --volume $PWD:/root/thermo:rw \
       --interactive \
       --tty \
       helics_thermostat \
       /bin/sh -c 'cd /root/thermo; exec "./run_helics.sh"'
