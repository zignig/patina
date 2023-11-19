cargo objcopy --release -- -O binary stuff.bin
./hapenny-montool /dev/ttyUSB0 ping
./hapenny-montool /dev/ttyUSB0 write 0 stuff.bin
./hapenny-montool /dev/ttyUSB0 call 0 
screen /dev/ttyUSB0 115200
