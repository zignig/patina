cargo objcopy --release --bin console -- -O binary load.bin
./hapenny-montool /dev/ttyUSB0 run load.bin
screen /dev/ttyUSB0 115200 
