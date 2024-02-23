cargo objcopy --release --bin console -- -O binary load.bin
./hapenny-montool -b 115200 /dev/ttyUSB0 run load.bin
screen /dev/ttyUSB0 115200 
