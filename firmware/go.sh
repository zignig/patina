# build an named binary and upload it to the core
arg1=${1:-console}
cargo objcopy --release --bin $arg1 -- -O binary bin/$arg1 && ../loader.py -f bin/$arg1
