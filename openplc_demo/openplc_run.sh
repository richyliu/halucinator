#!/usr/bin/env bash

cd "$(dirname "$0")"

ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -g)
            shift
            ARGS+=(--gdb_server_port 3333)
            ;;
        -t)
            shift
            ARGS+=(--log_blocks=regs)
            ;;
        *)
            ARGS+=("$1")
            ;;
    esac
    shift
done

ARGS+=(--config openplc_config.yaml)
ARGS+=(--config openplc_addrs.yaml)
ARGS+=(--config openplc_memory.yaml)
ARGS+=(--name openplc)

halucinator "${ARGS[@]}"
