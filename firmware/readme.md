# firmware testing 

it seems to be possible to run on qemu

- qemu-system-riscv32 -machine virt -m 128 -device ramfb -serial stdio -bios none -kernel
- https://github.com/SimonSapin/riscv-qemu-demos