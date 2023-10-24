# Minimal RISCV runtime

build environment for riscv32i on (https://github.com/cbiffle/hapenny)

An attempt at a minimal rust riscv framework for fpga control plane development 

## Commands 

cargo objcopy --release --bin rustv -- -O ihex test.hex

cargo rustc --release -- --emit asm

cargo objdump --release -- --disassemble --no-show-raw-insn -


