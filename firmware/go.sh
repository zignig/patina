arg1=${1:-console}
cargo objcopy --release --bin $arg1 -- -O binary $arg1.bin && ../loader.py -f $arg1.bin
