cargo objcopy --release --bin mini -- -O binary load.bin
./hapenny-montool /dev/ttyUSB0 run load.bin
screen /dev/ttyUSB0 115200 
