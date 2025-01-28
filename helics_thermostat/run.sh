#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

halucinator -c=config.yaml -c addrs.yaml -c memory.yaml --log_blocks=trace -n thermostat "$@"
