//! some asm to set up the risc-v machine

//use crate::println;
//use crate::uart::{Bind, DefaultSerial};
use core::arch::asm;
use core::arch::global_asm;

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

/// Crappy wait , just wastes tiime
#[inline(never)]
pub fn wait(dur: u32) {
    for _ in 0..dur {
        unsafe {
            asm!("nop");
        }
    }
}

/// Jump to the reset vector (reboot the processor)
#[allow(unused_assignments)]
pub fn reset() {
    // return to the bootloader
    let mut a: *mut u32 = core::ptr::null_mut();
    a = crate::generated::RESET_VECTOR as _;
    unsafe {
        core::arch::asm!(
        "
        jr {}               # activate 
        ",
            in(reg) a,
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
        //println!("GURU MEDITATION\r\n");
        reset();
    }
}


/// heap start ( end of the program 4 byte aligned)
/// no alloc yet , good for  flash boot testing as  it
/// is below the exisiting code
#[inline]
pub fn heap_start() -> *mut u32 {
    unsafe extern "C" {
        unsafe static mut __sheap: u32;
    }

    #[allow(unused_unsafe)] // no longer unsafe since rust 1.82.0
    unsafe {
        core::ptr::addr_of_mut!(__sheap)
    }
}