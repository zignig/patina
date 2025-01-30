# Firmware

This is basically my test space for an interface test SOC.


# Flash testing

Putting some data into the flash for read  testing. 

figlet " Patina "  | cowsay -f turtle -n > test.bit

warmboot the pooter: 

tinyprog -u test.bit 

this is posted at 0x50000 

get the length from ls -la of test.bit ( for now )


# Dump assembly for a binary ( and learn to read ;) 

cargo objdump --release --bin base -- --disassemble --no-show-raw-insn
