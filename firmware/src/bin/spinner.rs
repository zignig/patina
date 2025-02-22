#![no_std]
#![no_main]

use patina_pac::init::{reset, wait};



// For Simulation testing
#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut counter: u32 = 0;
    loop {
        counter += 1;
        wait(1000);
    }
}
