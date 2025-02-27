#![no_std]
#![no_main]

use patina_pac::init::wait;
// Amcsr bus on this test rig
// pub const AMCSR_ADDR: u32 = 2048;
// pub const AMCSR_END: u32 = 2096;
pub const LED: u32 = 4096;
// For Simulation testing
#[no_mangle]
pub extern "C" fn main() -> ! {
    // let mut counter: u32 = AMCSR_ADDR;
    let mut addr: *mut u32 = core::ptr::null_mut();
    addr = LED as _;
    // wait(1000);
    loop {
        unsafe {
            addr.write_volatile(0);
        };
        wait(32);
        unsafe {
            addr.write_volatile(32);
        };
        wait(31);
        unsafe {
            let _word = addr.read_volatile();
        }
    }
}
