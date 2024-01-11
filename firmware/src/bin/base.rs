#![no_std]
#![no_main]
#![feature(strict_provenance)]

use rustv::init::reset;
use rustv::println;
use rustv::uart::{DefaultSerial,Bind};


#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serial port
    let mut ds = DefaultSerial::new();
    println!("Base testing\r\n");
    loop {
        for _ in 1..50 {
            for char in 32..126 {
                ds.putb(char);
            }
        }
        reset();
    }
}
