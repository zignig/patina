#![no_std]
#![no_main]

use heapless::String;

use rustv::init::{reset, wait};
use rustv::println;
use rustv::uart::{Bind, DefaultSerial};

const PROMPT: &str = ">>";

// Default reset from build system (.cargo/config.toml)
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

struct Buffer {
    data: String<16>,
    cursor: usize,
}

impl Buffer {
    fn new() -> Self {
        Self {
            data: String::new(),
            cursor: 0,
        }
    }

    fn reset(&mut self) {
        self.data.clear();
        self.cursor = 0;
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
    let intro = "Welcome to new patina";
    println!("{}\r\n", intro);
    println!("{}", PROMPT);
    loop {
        if let Some(c) = ds.get() {
            match c {
                b'\x03' => {
                    // Control C
                    println!("\r\n{}", PROMPT);
                }
                b'\x04' => {
                    // Control D
                    reset()
                }
                b'\x0D' => {
                    // Enter
                    let data = buffer.data.as_str();
                    run_command(data);
                    buffer.reset();
                    println!("\r\n{}", PROMPT);
                }
                b'\x21' => {
                    // ! ( exclaimation )
                    println!("BORK\r\n");
                    list()
                }
                _ => {
                    ds.putb(c);
                    let _ = buffer.data.push(c as char);
                }
            }
        }
    }
}

fn list() {
    let len = COMMANDS.len();
    for i in 0..len {
        println!("{} = {}\r\n", i, *COMMANDS[i].0);
    }
}

fn run_command(data: &str) {
    let mut ctx = Ctx::new();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        for (name, imp) in COMMANDS {
            if *name == cmd {
                imp(&mut ctx);
                return;
            }
        }
    }
    println!("end\r\n");
}
struct Ctx {}

impl Ctx {
    fn new() -> Self {
        Self {}
    }
}

type Command = fn(&mut Ctx);

static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("info", cmd_empty),
    ("other", cmd_empty),
    ("reset", cmd_reset),
    // ("reboot", cmd_empty),
];

#[inline(never)]
fn cmd_empty(_ctx: &mut Ctx) {
    println!("empty command");
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}
