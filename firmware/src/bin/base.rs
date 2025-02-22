#![no_std]
#![no_main]

use patina_pac::{
    init::reset,
    uart::{Bind, DefaultSerial},
    warmboot::Warm,
};

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Create the warmboot device
    let mut warmboot = Warm::new();
    // Create a serial port
    let mut ds = DefaultSerial::new();
    loop {
        if let Some(c) = ds.get() {
            match c {
                // ESC
                b'\x1b' => {
                    reset();
                }
                // Control D
                b'\x04' => {
                    warmboot.write();
                }
                //echo everything else
                _ => {
                    ds.putb(c);
                }
            }
        }
    }
}
