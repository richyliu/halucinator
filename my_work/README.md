# Thermostat demo

## Generating files

### Binary file

generate `target.bin` with
```sh
arm-none-eabi-objcopy -O binary thermometer_2024_spring.elf target.bin
```

### Addresses

to generate addrs.yaml, use `nm`
```sh
nm -an thermometer_2024_spring.elf | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}' >> addrs.yaml
```

one liner version to prepend with correct header:
```sh
{ base64 -d <<< YXJjaGl0ZWN0dXJlOiBBUk1FTApiYXNlX2FkZHJlc3M6IDAKZW50cnlfcG9pbnQ6IDAKc3ltYm9sczoK; nm -an thermometer_2024_spring.elf | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}'; }  > addrs.yaml
```

### Update inject with locations

Update inject/main.c with locations. Use the following command to get these locations:
```sh
nm -an thermometer_2024_spring.elf | grep -E '(htim16|HAL_TIM_PeriodElapsedCallback)'
```

### Update device.py with model values

Update the A and B constants used to calculate temperature from raw reading in device.py
