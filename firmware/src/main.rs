#![no_std]
#![no_main]
#![feature(strict_provenance)]

use core::str;

mod uart;
use uart::Bind;

use crate::uart::DefaultSerial;

mod init;
use init::{wait,reset};

use heapless::String;


// Default reset from build system (.cargo/config.toml)
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

struct Buffer { 
    data: String<64>,
    cursor: usize,
}

impl Buffer {
    fn new() -> Self {
        Self{
            data: String::new(),
            cursor: 0 
        }
    }

    fn reset(&mut self) { 
        self.data.clear();
        self.cursor = 0 ;
    }
}


#[no_mangle]
pub extern "C" fn main() -> ! {
    // Some heapless constructs 
    let mut buffer = Buffer::new();

    //Create a serai port
    let mut ds = DefaultSerial::new();
    // Delay
    wait(60000);
    let intro =  "Welcome to new patina";
    println!("{}",intro);
    
    loop {
        if let Some(c) = ds.get() {
            ds.putb(c);
            let _ = buffer.data.push(c as char);

            if c == b'`' {
                reset();
            }
            if c == b'w' {
                list();
            }
            if c == b'\n' {
                println!("{}",buffer.data.as_str());
                buffer.reset();
            }
        }
    }
}

fn list() {
    for (name, _, _) in COMMANDS {
        //println!("{}",name);
        println!("-{}",name);
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
