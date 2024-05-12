//! Firware library for the patina soc core
#![no_std]
#![feature(iter_array_chunks)]
#![feature(iter_next_chunk)]

#![deny(missing_docs)]

/// This file is templated in patina/generated/variables.py
/// made from the SOC memory map.
pub mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub mod init;
pub mod uart;
pub mod readline;
pub mod terminal;
pub mod flash;
