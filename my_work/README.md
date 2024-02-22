generate `target.bin` with
```sh
arm-none-eabi-objcopy -O binary thermometer_2024_spring.elf target.bin
```

to generate addrs.yaml, use `nm`
```sh
nm -an thermometer_2024_spring.elf | grep '0800.* . .\{5,\}' | awk -F' ' '{print "  0x" $1 ": " $3}' >> addrs.yaml
```
