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
pub fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}

#[allow(unused_assignments,)]
pub fn reset() {
    // return to the bootloader
    let mut a: *mut u32 = core::ptr::null_mut();
    a = crate::generated::RESET_VECTOR as _ ;
    unsafe {
        core::arch::asm!(
        "
        jr a0               # activate bootloader
        ",
            in("a0") a,
            options(noreturn),
        );
    }
}

// -- no interupts yet.
#[no_mangle]
#[allow(non_snake_case)]
fn DefaultInterruptHandler() {}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    loop {
        reset();
    }
}
