#![no_std]
#![no_main]
//#![feature(start)]
#![feature(strict_provenance)]

use core::arch::asm;
use core::arch::global_asm;

// extern crate riscv_rt;
// use riscv_rt::entry;

const LED_ADDRESS: u32 = 8192 + 4; // one word past the end of memory.

struct Led {
    address: u32,
}

impl Led {
    fn new(address: u32) -> Self {
        Self { address: address }
    }

    pub fn on(&mut self) {
        unsafe {
            (self.address as *mut u32).write_volatile(1);
        }
    }

    pub fn off(&mut self) {
        unsafe {
            (self.address as *mut u32).write_volatile(0);
        }
    }
}

//

// #[entry]
// fn main() -> ! {
//     let mut blink = Led::new(LED_ADDRESS);
//     loop {
//         blink.off();
//         wait(u32::MAX);
//         blink.on();
//     }
// }

global_asm!(
    "
    .option norvc
    # the .init section gets linked about .text
    .section .init, \"ax\" ,@progbits
    .global _start
    .global abort
    
    _start:
        #lui     a0, %hi(boot_time_trap_handler)
        #addi    a0, a0, %lo(boot_time_trap_handler)
        #slli    a0, a0, 2
        #csrrs   x0, stvec, a0
        
        la       sp, _stack_start
        j        __start_rust
    
    .option norvc
    ",
);

#[no_mangle]
//#[start]
pub unsafe extern "C" fn __start_rust() -> ! {
    let mut blink = Led::new(LED_ADDRESS);
    loop {
            wait(u32::MAX);
            blink.off();
            wait(u32::MAX);
            blink.on();
    }
}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

#[no_mangle]
#[allow(non_snake_case)]
fn DefaultInterruptHandler() {}


//#[inline(never)]
fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}
