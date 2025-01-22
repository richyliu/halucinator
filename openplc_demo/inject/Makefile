
all: main.elf

main.elf: main.c main.map
	arm-none-eabi-gcc main.c -march=armv6-m -Xlinker -Map=main.map -o main.elf -Os
