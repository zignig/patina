#![no_std]
// features 

#![feature(iter_array_chunks)]
#![feature(iter_next_chunk)]

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
pub mod watchdog;
#[cfg(feature= "flash")]
pub mod flash;