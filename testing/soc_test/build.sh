python regstuff.py
cargo init test_pac --lib
svd2rust -i soc.svd -o test_pac/src/ --target riscv
cd test_pac
#form -i lib.rs -o src/
rm lib.rs
cargo fmt
cargo add vcell
cargo add critical-section
cargo add riscv
cargo add riscv-rt
