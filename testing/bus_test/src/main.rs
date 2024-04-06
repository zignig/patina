#![no_std]
#![no_main]

use core::arch::asm;
use core::arch::global_asm;

#[no_mangle]
pub extern "C" fn main() -> ! {
    loop {}
}

// -- no interupts yet.
#[no_mangle]
#[allow(non_snake_case)]
fn DefaultInterruptHandler() {}

global_asm! {
    "
    .pushsection .start,\"ax\",%progbits
    .globl __start
    __start:
        j main
    .popsection
    "
}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe {
        asm! {
            "li t1, 0",
            "li t2, 3"
        };
    }
    loop {}
}
