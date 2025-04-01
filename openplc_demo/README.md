# OpenPLC Halucinator demo

Easiest way to set up is with docker. Use the docker file in the top level of the directory (../openplc_demo.Dockerfile). Before that, be sure to clone this repository and submodules:
```sh
git clone <this repo>
git submodule update --init
cd deps/avatar-qemu && git submodule update --init
```

The included openplc_target.bin contains seal-in flip-flop logic with pin 90 being set, pin 93 being reset, and pin 36 being the output.

## Building OpenPLC code

The project is in `openplc_project/`. Use the "STM32 F446ZET Nucleo" target to build (click "Transfer program to PLC", choose the right Board Type, select "Compile Only", and click "Compile"). Output ELF will be in the indicated directory.

Copy the file out (from /root/Downloads/OpenPLC_Editor/editor/arduino/examples/Baremetal/build).

## Setting up the demo

Run `./setup_openplc_bin.sh <ELF>` to convert the ELF program to a raw binary file for halucinator to use. This also updates the openplc_addrs.yaml file with the correct addresses based on the symbols.
