# firmware testing 

it seems to be possible to run on qemu

- qemu-system-riscv32 -machine virt -m 128 -device ramfb -serial stdio -bios none -kernel
- https://github.com/SimonSapin/riscv-qemu-demos

# Flash testing

Putting some data into the flash for read  testing. 

figlet " Patina "  | cowsay -f turtle -n > test.bit

warmboot the pooter: 

tinyprog -u test.bit 

this is posted at 0x50000 

get the length from ls -la of test.bit ( for now )

