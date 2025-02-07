use std::path::PathBuf;
use std::fs;
use std::env;

fn main() {
    // Generate the files

    // generated file include
    let output_path = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    fs::write(output_path.join("generated.rs"), include_bytes!("generated.rs")).unwrap();

    // Put the linker script somewhere the linker can find it.
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    fs::write(out_dir.join("memory.x"), include_bytes!("memory.x")).unwrap();

    println!("cargo:rerun-if-changed=memory.x");
    println!("cargo:rerun-if-changed=generated.rs");
}
