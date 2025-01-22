#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

halucinator -c=openplc_config.yaml -c openplc_addrs.yaml -c openplc_memory.yaml --log_blocks=trace -n openplc "$@"
