#![no_std]
#![no_main]
#![feature(strict_provenance)]


use core::str;

mod uart;
use uart::{Serial,Bind};

use crate::uart::DefaultSerial;

mod init;


#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serai port 
    let serial = DefaultSerial::new();
    //println!("Welcome to patina");
    loop {
        if let Some(c) = serial.get() {
            serial.put(c);
            if c == b'`' {
                reset();
            }
            if c == b'w' {
                list();
            }
        }
    }
}

fn list() {
    for (name, _, _) in COMMANDS {
        write(name);
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
}



fn reset() {
    // return to the bootloader
    let mut a: *mut u32 = core::ptr::null_mut();
    a = 8192 as _;
    unsafe {
        core::arch::asm!(
        "
        jr a0               # activate routine
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
    loop {}
}
