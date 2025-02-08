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

use rustv::{
    flash::Flash,
    generated,
    init::{heap_start, reset},
    println,
    uart::{Bind, DefaultSerial},
};

/// This constant is board specific , add the address and length to flash .rs
pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;

/// Main entry point
#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut flash: TinyFlash = Flash::new();
    //let mut ds = DefaultSerial::new();

    flash.wakeup();

    // const START: u32 = 0x50000;
    // const SIZE: u16 = 65000;
    let mut dst: *mut u32 = heap_start();
    dst = 0x1000 as _;
    // Load the first word from flash
    // length for now
    // FF 256 bytes , read words into ram
    // ... and boot
    //
    loop {
        let flash_len = flash.read_words(0x50000, 1).next().unwrap();
        //println!("{}", flash_len);
        for word in flash.read_words(0x50000 + 256, (flash_len) as u16) {
            unsafe {
                dst.write_volatile(word);
                dst = dst.add(1);
            }
            //println!("{}\r\n", word);
            //println!(".")
        }

        dst = 0x1000 as _;
        call(dst);
        //reset();
    }
}

fn call(addr: *mut u32) {
    unsafe {
        core::arch::asm!(
            "
        # restart monitor if program returns.
     1: auipc ra, %pcrel_hi(__start)
        addi ra, ra, %pcrel_lo(1b)

        jr {}               # activate routine
        ",
            in(reg) addr,
            options(noreturn),
        );
    }
}
