#![no_std]
#![feature(iter_array_chunks)]
#![feature(iter_next_chunk)]

pub mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub mod init;
pub mod uart;
pub mod readline;
pub mod terminal;
pub mod flash;
