#![no_std]
#![no_main]

use patina_pac::init::wait;

// Amcsr bus on this simulation rig
// Run on csr_sim.py

pub const AMCSR_ADDR: u32 = 2048;
pub const AMCSR_END: u32 = 2096;
pub const LED: u32 = 4096;
// For Simulation testing
#[no_mangle]
#[allow(unused_assignments)]
pub extern "C" fn main() -> ! {
    let mut addr: *mut u32 = core::ptr::null_mut();
    addr = LED as _;
    // let mut val: u32 = 0;
    loop {
        for counter in AMCSR_ADDR..AMCSR_END {
            addr = counter as _;
            for _j in 0..8 {
                unsafe {
                    addr.write_volatile(255);
                    let _ = addr.read_volatile();
                    addr.write_volatile(254);
                }
            }
        }
        wait(10);
    }
}
