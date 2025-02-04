#![no_std]
#![no_main]

use patina_pac::warmboot::Warmboot;
use rustv::init::reset;
use rustv::uart::{Bind, DefaultSerial};
use rustv::generated;

/// Internal warmboot device on the ice40
pub type ActualWarm = Warmboot<{ generated::WARMBOOT_ADDR }>;

#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut warmboot: ActualWarm = Warmboot::new();
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
                b'\x03' => {
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
