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
    init::reset,
    println,
    uart::{Bind, DefaultSerial},
};

// This is board specific , add the address and length to flash .rs

pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;

#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut flash: TinyFlash = Flash::new();
    //let mut ds = DefaultSerial::new();

    flash.wakeup();

    // const START: u32 = 0x50000;
    // const SIZE: u16 = 65000;
    let mut dst: *mut u32 = core::ptr::null_mut();
    dst = 0x1800 as _;
    let flash_len: u16; 
    loop {
        for word in flash.read_words(0x50000 + 256,10){
            unsafe {
                dst.write_volatile(word);
                dst = dst.add(1);
            }
            println!("{}\r\n",word);
        }
        // for words in flash.read_iter(0x50000, 4).array_chunks::<4>() {
        //     //println!("{:?}\r\n",words);
        //     let num: u32 = u32::from_le_bytes(words);
        //     println!("{:?}\r\n", num);
        // }
        // Load the first word from flash
        // length for now
        // FF 256 bytes , read words into ram
        // ... and boot
        //
        reset();
    }
}
