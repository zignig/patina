cargo objcopy --release --bin mini -- -O binary load.bin
./hapenny-montool -b 57600 /dev/ttyUSB0 run load.bin
screen /dev/ttyUSB0 57600 
