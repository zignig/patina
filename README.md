# Minimal RISCV runtime and build environment for 

(https://github.com/cbiffle/hapenny)

An attempt at a minimal rust riscv framework for fpga control plane development 

cargo objcopy --release --bin rustv -- -O ihex test.hex

cargo rustc --release -- --emit asm

cargo objdump --release -- --disassemble --no-show-raw-insn -


