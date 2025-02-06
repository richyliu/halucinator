# HELICS thermostat demo

## Setup

First, build the docker container from the root of this repository (not this directory).

```sh
docker build -t helics_thermostat -f helics_thermostat/Dockerfile .
```

## Running

Simply use the `./run_docker.sh` script in this directory to run.

## Configuration

Edit the `total_interval` variable in thermostat.py to control how long to simulate for.
