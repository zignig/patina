#![no_std]
#![no_main]

use patina_pac::init::wait;

// Amcsr bus on this simulation rig
// Run on csr_sim.py
pub const AMCSR_ADDR: u32 = 2048;
pub const AMCSR_END: u32 = 2056;
// For Simulation testing
#[no_mangle]
#[allow(unused_assignments)]

//
pub extern "C" fn main() -> ! {
    loop {

        let mut addr: *mut u32 = core::ptr::null_mut();
        addr = 2056 as _;
        unsafe { 
            addr.write_volatile(0x11223344);
        }
        
        wait(16);

        // Manual write of the overflow register
        let mut addr: *mut u16 = core::ptr::null_mut();

        addr = 2056 as _;

        unsafe {
            addr.write_volatile(0x11);
            addr = addr.add(1);
            addr.write_volatile(0x22);
            addr = addr.add(1);
            addr.write_volatile(0x33);
            addr = addr.add(1);
            addr.write_volatile(0x44);
        }
        loop{}
    }
}

// let mut val: u8 = 0x1;

// for val in 0..32 {
//     unsafe {
//         addr.write_volatile(val);
//         addr = addr.add(1);
//     }
//     // val += 1;
// }

//     // Enable the timer
//     addr = 2048 as _;
//     unsafe {
//         addr.write_volatile(1);
//     }


//         wait(4);
//         unsafe {
//             addr.write_volatile(0);
//         }
//     wait(4);
