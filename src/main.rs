#![no_std]
#![no_main]
#![feature(strict_provenance)]

use core::arch::asm;
use core::arch::global_asm;

mod uart;

// World's cheapest RISC-V "runtime" - only works because we don't use non-stack
// RAM (as ensured by our linker script)
global_asm! {
    "
    .pushsection .start,\"ax\",%progbits
    .globl __start
    __start:
        # initialize stack pointer
1:      auipc sp, %pcrel_hi(__stack_start)
        addi sp, sp, %pcrel_lo(1b)
        # No need to fill in a return address, main won't return
        j main

    .popsection
    "
}

#[no_mangle]
pub extern "C" fn main() -> ! {
    loop {
        wait(12345);
    }
}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    let mut val:u8;
    loop {
        val = uart::getc();
        uart::putb(val);
        wait(10);
    }
}

#[no_mangle]
#[allow(non_snake_case)]
fn DefaultInterruptHandler() {}


#[inline(never)]
fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}


