use std::env;
use std::fs;
use std::path::PathBuf;
use std::{env::VarError};
use std::io::Write;

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    // Put the linker script somewhere the linker can find it.
    fs::write(out_dir.join("memory.x"), include_bytes!("memory.x")).unwrap();
    println!("cargo:rustc-link-search={}", out_dir.display());
    println!("cargo:rerun-if-changed=memory.x");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=UART_ADDR");
    // serial port builder

    let addr_input = match std::env::var("UART_ADDR") {
        // Ugh why is this not an Option
        Err(VarError::NotPresent) => None,
        Ok(result) => Some(result),
        e => panic!("{:?}", e),
    };

    let addr = match addr_input {
        None => {
            println!("cargo:warning=note: UART address not provided, defaulting to 0x200");
            0x200
        }
        Some(text) => {
            parse_int::parse::<u32>(&text).unwrap()
        }
    };

    let mut out = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    out.push("peripherals.rs");

    let mut f = std::fs::File::create(&out).unwrap();
    writeln!(f, "pub const UART_ADDR: i16 = 0x{addr:x};").unwrap();
}
