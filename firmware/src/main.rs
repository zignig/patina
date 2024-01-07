#![no_std]
#![no_main]
#![feature(strict_provenance)]

<<<<<<< HEAD
mod readline;

mod terminal;

mod uart;
use uart::Bind;
=======
use core::{marker::PhantomData, str};

mod uart;
use uart::{ writer,Bind};
>>>>>>> bork

use crate::uart::DefaultSerial;

mod init;
use init::{reset, wait};

use heapless::String;

<<<<<<< HEAD
const PROMPT: &str = ">>";
=======
const PROMPT: &str = ">";
>>>>>>> bork

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
<<<<<<< HEAD
                31..=127 => {
                    ds.putb(c);
                    let _ = buffer.data.push(c as char);
                }
                _ => {}
=======
                b'\x21' => list(),
                _ => {
                    ds.putb(c);
                    let _ = buffer.data.push(c as char);
                }
>>>>>>> bork
            }
        }
    }
}

#[inline(never)]
fn list() {
    println!("START LIST\r\n");
    println!("len {}\r\n", COMMANDS.len());
    // let len = COMMANDS.len();
    // for i in 0..len{
    //     println!("{} = {}\r\n",i,*COMMANDS[i].0);
    // }
<<<<<<< HEAD
    for item in COMMANDS {
        println!("{}",&item.0);
=======
    for (name,_) in COMMANDS {
        writer(name);
>>>>>>> bork
    }
}

fn run_command(data: &str) {
<<<<<<< HEAD
    let mut ctx = Ctx::new("stuff");
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        println!("\r\n>>>{}<<<", cmd);
        for item in COMMANDS {
            if  item.0 == cmd {
                println!("MATCH\r\n{}",item.0);
                item.1(&mut ctx);
=======
    let mut ctx = Ctx::new();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        println!("\r\n>>>{}<<<", cmd);
        for (name, imp) in COMMANDS {
            if *name == cmd {
                println!("MATCH\r\n");
                imp(&mut ctx);
>>>>>>> bork
                return;
            }
        }
    }
    println!("end\r\n");
}
struct Ctx {
<<<<<<< HEAD
    data: String<8>
}

impl Ctx {
    fn new(name: &str) -> Self {
        let name_as_str = String::try_from(name).unwrap();
        Self{
            data: name_as_str
        }
=======

}

impl Ctx {
    fn new() -> Self {
        Self{}
>>>>>>> bork
    }
}

type Command = fn(&mut Ctx);

<<<<<<< HEAD
struct CommandItem(&'static str, Command);

static COMMANDS: &[CommandItem] = &[
    CommandItem("list", cmd_list),
    CommandItem("info", cmd_empty),
    //("other", cmd_empty),
    //("reset", cmd_empty),
    // ("reboot", cmd_empty),
=======
static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("info", cmd_empty),
    ("other", cmd_empty),
    //("reset", cmd_empty),
      // ("reboot", cmd_empty),
>>>>>>> bork
];


#[inline(never)]
<<<<<<< HEAD
fn cmd_empty(ctx: &mut Ctx) {
    println!("empty command as {}",ctx.data.as_str());
}

fn cmd_list(_ctx: &mut Ctx) {
    println!("list the commands");
=======
fn cmd_empty(_ctx: &mut Ctx) {
    println!("empty command");
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
>>>>>>> bork
}
