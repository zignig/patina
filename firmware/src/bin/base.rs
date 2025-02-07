#![no_std]
#![no_main]

use patina_pac::warmboot::Warm;
use patina_pac::init::reset;
use patina_pac::uart::{Bind, DefaultSerial};

#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut warmboot = Warm::new();
    //Create a serial port
    let mut ds = DefaultSerial::new();
    loop {
        if let Some(c) = ds.get() {
            match c {
                // 32 => {
                //     for char in 31..126 {
                //         ds.putb(char);
                //     }
                // }
                b'\x1b' => {
                    reset();
                }
                b'\x04' => {
                    warmboot.write();
                }

                _ => {
                    //echo everything else
                    ds.putb(c);
                }
            }
        }
    }
}
