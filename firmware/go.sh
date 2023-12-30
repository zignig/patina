cargo objcopy --release -- -O binary stuff.bin
./hapenny-montool /dev/ttyUSB0 -b 19200 run stuff.bin
screen /dev/ttyUSB0 19200 
