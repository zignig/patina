#![no_std]

use core::arch::asm;

// Crappy wait
#[inline(never)]
pub(crate) fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}

pub mod generated {
    use core::{include,concat,env};
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub mod flash;