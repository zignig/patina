#![no_std]
#![no_main]
#![feature(iter_array_chunks)]

//! this is a test bootstrap for spi boot
//! read the first word (4 bytes) from flash.
//! FF to 256 bytes , 1 page and load words into
//! ram from flash.
//!
//! The extended boot loader should have standard serial bootloader
//! time out after ~seconds(ish) and read from flash
//!

use patina_pac::flash;
use patina_pac::init::heap_start;

/// Main entry point
#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut flash = flash::Flash::new();

    flash.wakeup();

    // const START: u32 = 0x50000;
    // const SIZE: u16 = 65000;
    let mut dst: *mut u32 = heap_start();
    // Load the first word from flash
    // length for now
    // FF 256 bytes , read words into ram
    // ... and boot
    //
    loop {
        let flash_len = flash.read_words(0x50000, 1).next().unwrap();
        for word in flash.read_words(0x50000 + 256, (flash_len) as u16) {
            unsafe {
                dst.write_volatile(word);
                dst = dst.add(1);
            }
        }
        call_jump(dst);
    }
}

#[allow(unused_assignments)]
fn call_jump(addr: *mut u32) {
    // Jump into the new program
    let mut a: *mut u32 = core::ptr::null_mut();
    a = addr as _;
    unsafe {
        core::arch::asm!(
        "
            jr {}               # activate 
            ",
            in(reg) a,
            options(noreturn),
        );
    }
}
