#![no_std]
#![no_main]
#![feature(strict_provenance)]


use rustv::uart::{Bind, DefaultSerial};
use rustv::println;
use rustv::init::{reset, wait};

use heapless::String;

const PROMPT: &str = ">";

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
    println!("{}", intro);
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
                    println!("\r\n>>{}<<", data);
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
                    //ds.putb(c);
                    println!("0x{:x}\r\n",c);
                    let _ = buffer.data.push(c as char);
                }
            }
        }
    }
}

static SOME_STRING: &[&str] = &["one", "two", "three"];

// #[inline(never)]
fn list() {
    println!("START LIST\r\n");
    println!("len {}\r\n", SOME_STRING.len());
    // let len = COMMANDS.len();
    // for i in 0..len{
    //     println!("{} = {}\r\n",i,*COMMANDS[i].0);
    // }
    for name in SOME_STRING{ 
        println!("bork\r\n")
        //println!("{}\r\n",name);
    }

}

fn run_command(data: &str) {
    let mut ctx = Ctx::new();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        println!("\r\n>>>{}<<<", cmd);
        for (name, imp) in COMMANDS {
            if *name == cmd {
                println!("MATCH\r\n");
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
    //("reset", cmd_empty),
    // ("reboot", cmd_empty),
];

#[inline(never)]
fn cmd_empty(_ctx: &mut Ctx) {
    println!("empty command");
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}
