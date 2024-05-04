arg1=${1:-console}
cargo objcopy --release --bin $arg1 -- -O binary load.bin && ../loader.py
