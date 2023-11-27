//! some asm to set up the risc-v machine

use core::arch::global_asm;
use core::arch::asm;

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

// Crappy wait
#[inline(never)]
fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}
