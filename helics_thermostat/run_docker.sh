#!/usr/bin/env bash

set -ex

cd "$(dirname "$0")"

docker run \
       --rm \
       --volume $PWD:/root/thermo:rw \
       --interactive \
       --tty \
       helics_thermostat \
       /root/thermo/run_helics.sh
