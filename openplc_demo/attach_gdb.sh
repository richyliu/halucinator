#!/usr/bin/env bash

gdb-multiarch \
    --quiet \
    --eval-command='target remote localhost:3333' \
    --eval-command='set confirm off' \
    Baremetal.ino.elf
    # --eval-command='handle SIGINT nostop noprint pass' \
