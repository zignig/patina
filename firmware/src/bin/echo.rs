#![no_std]
#![no_main]

use patina_pac::init::reset;
use patina_pac::uart::{Bind, DefaultSerial};

#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serial port
    let mut ds = DefaultSerial::new();
    loop {
        if let Some(c) = ds.get() {
            match c {
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
