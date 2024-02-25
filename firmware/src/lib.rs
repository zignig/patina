#![no_std]

mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

pub mod init;
pub mod uart;
pub mod readline;