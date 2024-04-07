#![no_std]

pub mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub mod init;
pub mod uart;
pub mod readline;
pub mod terminal;
pub mod warmboot;
pub mod led;
pub mod input;