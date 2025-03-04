#![no_std]
#![no_main]
#[allow(unused_imports)]
// use patina_pac::generated;
use patina_pac::init::wait;

#[allow(dead_code)]
mod generated;

// Amcsr bus on this simulation rig
// Run on csr_sim.py
pub const U8REG: u32 = 2048;
pub const U8REG_T: u32 = 2052;
// For Simulation testing
#[unsafe(no_mangle)]
#[allow(unused_assignments)]
#[allow(unused_variables)]
pub extern "C" fn main() -> ! {
    loop {
        // ! byte reads and writes

        // write to the register
        // let transfer: u8 = 0;
        // let mut addr: *mut u8 = core::ptr::null_mut();
        // addr = U8REG as _;

        // write_reg(generated::TIMER_OVF_ADDR+4,0x11223344);
        // let mut addr2: *mut u8 = core::ptr::null_mut();
        // addr2 = U8REG_T as _;


        // unsafe {
        //     addr.write_volatile(0x55);
        // }

        // unsafe {
        //     let _ = addr.read_volatile();
        // }

        // Write back to the second register
        // unsafe {
        //     addr2.write_volatile(transfer + 2);
        // }
        // let mut addr: *mut u16 = core::ptr::null_mut();
        // addr = AMCSR_ADDR as _ ;
        // unsafe {
        //     addr.write_volatile(0xBB);
        //     let _ = addr.read_volatile();
        // }
        let mut addr: *mut u8 = core::ptr::null_mut();
        addr = generated::REGTEST_U8_ADDR as _ ;
        let mut val:u8 = 0xAA;
        for _ in 0..32 {
            unsafe {
                addr.write_volatile(val);
                addr = addr.add(1);
            }
            val += 1;
        }
        wait(5);

        // let mut addr: *mut u32 = core::ptr::null_mut();
        // addr = 2056 as _;
        // unsafe {
        //     addr.write_volatile(0x11223344);
        // }

        // wait(16);

        // Manual write of the overflow register
        // let mut addr: *mut u16 = core::ptr::null_mut();

        // addr = 2056 as _;

        // unsafe {
        //     addr.write_volatile(0x00);
        //     addr = addr.add(1);
        //     addr.write_volatile(0xFF);
        //     addr = addr.add(1);
        //     addr.write_volatile(0x00);
        //     addr = addr.add(1);
        //     addr.write_volatile(0x00);
        // }
        loop {}
    }
}

// fn enable(val: bool) {
//     // Enable the timer
//     let mut addr: *mut u8 = core::ptr::null_mut();
//     addr = 2048 as _;
//     unsafe {
//         if val {
//             addr.write_volatile(1);
//         } else {
//             addr.write_volatile(0);
//         }
//     }
// }

fn write_reg(address: u32, value: u32) {
    let mut addr: *mut u8 = core::ptr::null_mut();
    addr = address as _;
    for v in value.to_le_bytes() {
        unsafe {
            addr.write_volatile(v);
            addr = addr.add(2);
        }
    }
}
//         wait(4);
//         unsafe {
//             addr.write_volatile(0);
//         }
//     wait(4);

// let mut val: u8 = 0x1;

// for val in 0..32 {
//     unsafe {
//         addr.write_volatile(val);
//         addr = addr.add(1);
//     }
//     // val += 1;
// }
