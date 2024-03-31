#![no_std]
#![no_main]

use rustv::init::reset;
use rustv::uart::{Bind, DefaultSerial};

#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serial port
    let mut ds = DefaultSerial::new();
    loop {
        if let Some(c) = ds.get() {
            match c {
                32 => {
                    for char in 32..126 {
                        ds.putb(char);
                    }
                }
                b'\x04' => {
                    reset();
                }
                _ => {
                    //echo everything else
                    ds.putb(c);
                }
            }
        }
    }
}
