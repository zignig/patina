#![no_std]

/// This file is templated in patina/generated/variables.py
/// made from the SOC memory map.
pub mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub mod init;
pub mod led;
pub mod input;
#[cfg(feature = "warmboot")]
pub mod warmboot;
pub mod uart;

