#![no_std]
#![no_main]
#![feature(strict_provenance)]

use core::str;

mod uart;
use uart::{Bind,write};

use crate::uart::DefaultSerial;

mod init;
use init::{wait,reset};

#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serai port
    let mut ds = DefaultSerial::new();
    wait(10000);
    let intro =  "Welcome to patina";
    write(intro);
    loop {
        if let Some(c) = ds.get() {
            ds.putb(c);
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
        //println!("{}",name);
        write(name);
    }
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
fn cmd_empty(_ctx: &mut Ctx, _extra: &str) {}
