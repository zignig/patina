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
    data: String<32>,
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

pub enum Console { 
    Char,
    Up,
    Down,
    Left,
    Right,
    Home,
    Insert,
    Delete,
    PgUp,
    PgDown,
    Escape,
    Tab,
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
                // \x1b
                b'\x1b' => {
                    // cursor keys
                    if let Some(c) = ds.tget() {
                        match c {
                            b'\x5b' => {
                                if let Some(c) = ds.tget() {
                                    match c {
                                        b'\x41' => {
                                            println!("up");
                                        }
                                        b'\x42' => { 
                                            println!("down");
                                        }
                                        b'\x43' => { 
                                            println!("right");
                                        }
                                        b'\x44' => { 
                                            println!("left");
                                        }
                                        b'\x31' => {
                                            if let Some(c) = ds.tget(){
                                                println!("home{}",c);
                                            }
                                        }
                                        b'\x32' => {
                                            if let Some(c) = ds.tget(){
                                                println!("insert{}",c);
                                            }
                                        }
                                        b'\x33' => {
                                            if let Some(c) = ds.tget(){
                                                println!("delete{}",c);
                                            }
                                        }
                                        b'\x34' => {
                                            if let Some(c) = ds.tget(){
                                                println!("end{}",c);
                                            }
                                        }
                                        b'\x35' => {
                                            if let Some(c) = ds.tget(){
                                                println!("pg up{}",c);
                                            }
                                        }
                                        b'\x36' => {
                                            if let Some(c) = ds.tget(){
                                                println!("pg down{}",c);
                                            }
                                        }
                                        
                                        _ => {
                                            println!("c, <{:x}>", c);
                                        }
                                    }
                                }
                            }
                            _ => {
                                println!("unknown, <{:x}>", c);
                            }
                        }
                        println!("\r\n");
                    } else {
                        println!("escape only")
                    }
                }
                _ => {
                    ds.putb(c);
                    //println!(">{}<\r\n", c);
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
                println!("\r\n");
                imp(&mut ctx);
                return;
            }
        }
        println!("\r\nCommand not found \"{}\"", &cmd);
    }
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
    ("help", cmd_help),
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

fn cmd_help(_ctx: &mut Ctx) {
    println!("This is some unhelpful help");
}
