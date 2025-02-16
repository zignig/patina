#![no_std]
#![no_main]

use patina_pac::{
    init::reset,
    uart::{Bind, DefaultSerial},
    println,
    warmboot::Warm,
};

use ascii;
#[no_mangle]
pub extern "C" fn main() -> ! {
    let t = ascii::AsciiStr::from_ascii("test").unwrap();
    println!("{}",t);
    let mut warmboot = Warm::new();
    let mut ds = DefaultSerial::new();
    loop {
        if let Some(c) = ds.get() {
            match c {
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
