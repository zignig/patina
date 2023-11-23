// Simple uart functions

// The uart address is generted by the build script
//use core::write;

mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

const UARTRX: *mut i16 = generated::UART_ADDR as _;
const UARTTX: *mut u16 = (generated::UART_ADDR + 2) as _;

pub fn txbusy() -> bool {
    unsafe {
        UARTTX.read_volatile() != 0
    }
}

pub fn flush() {
    while txbusy() {
        // spin
    }
}

pub fn putb(b: u8) {
    flush();
    unsafe {
        UARTTX.write_volatile(u16::from(b));
    }
}

// Blocking Char read
#[inline(never)]
pub fn getc() -> u8 {
    loop {
        let status = unsafe { UARTRX.read_volatile() };
        if status >= 0 {
            return status as u8;
        }
    }
}

pub fn get() -> Option<u8> { 
    let status = unsafe { UARTRX.read_volatile() };
    if status >= 0 {
        return Some(status as u8);
    } 
    None
}