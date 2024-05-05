arg1=${1:-console}
cargo objcopy --release --bin $arg1 -- -O binary $arg1 && ../loader.py -f $arg1
