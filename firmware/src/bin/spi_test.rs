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
    let mut ds = DefaultSerial::new();

    flash.wakeup();

    //const SIZE: u16 = 1290;
    const START:u32 = 0x50000;
    const SIZE:u16 = 65000;

    loop {
        // Load the first word from flash 
        // length for now
        // FF 256 bytes , read words into ram
        // ... and boot
        // 

        // Load first word
        let length: u32 = flash.read_word(0x0);
        
        println!("\r\ndone\r\n");
        reset();
    }
}
