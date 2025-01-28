#!/usr/bin/env bash

bin="$1"
output_bin="openplc_target.bin"
addrs_yaml="openplc_addrs.yaml"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 ELF"
  exit 1
fi

set -ex

arm-none-eabi-objcopy -O binary "$bin" "$output_bin"
{ base64 -d <<< YXJjaGl0ZWN0dXJlOiBBUk1FTApiYXNlX2FkZHJlc3M6IDAKZW50cnlfcG9pbnQ6IDAKc3ltYm9sczoK; nm -an "$bin" | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}'; }  > "$addrs_yaml"

