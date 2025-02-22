# Minimal RISCV runtime

build environment for riscv32i on (https://github.com/cbiffle/hapenny)

An attempt at a minimal rust riscv framework for fpga control plane development 

# Overview 



# Installation

This project uses pdm so running `pdm install` should install all the python packages that are needed.

For the bootloader and the firmware a rust install for riscv32i-unknown-none-elf. 

# on the rust side

$ cargo install cargo-binutils
$ cargo install cargo-bloat

$ rustup component add llvm-tools

# pdm entry

to enter the PDM venv from the command line 

eval $(pdm venv activate in-project)
. .env.toolchain
