# Thermostat demo

## Generating files

generate `target.bin` with
```sh
arm-none-eabi-objcopy -O binary thermometer_2024_spring.elf target.bin
```

to generate addrs.yaml, use `nm`
```sh
nm -an thermometer_2024_spring.elf | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}' >> addrs.yaml
```

one liner version to prepend with correct header:
```sh
{ base64 -d <<< YXJjaGl0ZWN0dXJlOiBBUk1FTApiYXNlX2FkZHJlc3M6IDAKZW50cnlfcG9pbnQ6IDAKc3ltYm9sczoK; nm -an thermometer_2024_spring.elf | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}'; }  > addrs.yaml
```

## Necessary steps

- generate binary files
- update inject/main.c with locations
