#![no_std]
#![no_main]
#![feature(strict_provenance)]

use core::arch::asm;
use core::arch::global_asm;
use core::str;

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
        // val = uart::getc();
        // uart::putb(val);
        // wait(10);

        for (name, _, _) in COMMANDS {
            write(name);
        }
        wait(u32::MAX);
    }
}

#[inline(never)]
fn write(name: &str) {
    for c in name.as_bytes() {
        uart::putb(*c);
    }
    uart::putb(b'\n');
    uart::putb(b'\r');
}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

struct Ctx {
    data: str,
}

type Command = fn(&mut Ctx, &str);

static COMMANDS: &[(&str, Command, &str)] = &[
    ("list", cmd_empty, "print names"),
    ("info", cmd_empty, "print a summary of a type"),
    ("other", cmd_empty, "other stuff"),
    ("reset", cmd_empty, "other stuff"),
    ("reboot", cmd_empty, "other stuff"),
];

#[inline(never)]
fn cmd_empty(_ctx: &mut Ctx, _extra: &str) {
    uart::putb(0);
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
