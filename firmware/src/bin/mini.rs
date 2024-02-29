#![no_std]
#![no_main]

use rustv::init::{reset, wait};
use rustv::println;
use rustv::readline;
use rustv::terminal;
use rustv::uart::{Bind, DefaultSerial};

const PROMPT: &str = ">>";

// Default reset from build system (.cargo/config.toml)
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

// Primary data construct
// Add more to me and it is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: usize,
}

impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 10,
        }
    }
}

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(60000);
    let intro = "Welcome to new patina";
    println!("{}\r\n\r\n", intro);
    println!("{}", PROMPT);
    let mut counter: u32 = 0;
    let mut ctx = Ctx::new();
    loop {
        use readline::ConsoleAction::*;
        if let Some(val) = ctx.cons.process() {
            {
                match val {
                    Tab => {
                        println!("\r\n");
                        println!("Commands: \r\n");
                        list();
                    }
                    Cancel => {
                        ctx.cons.clear_screen();
                    }
                    Reset => {
                        reset();
                    }
                    Enter => {
                        run_command(&mut ctx);
                        ctx.cons.reset();
                        println!("\r\n{}", PROMPT);
                    }
                    //BackSpace => todo!(),
                    _ => println!("|{:?}", val),
                }
                counter = 0;
            }
        }
        // bug out timer
        counter = counter + 1;
        if counter > 6000_000_0 {
            println!("bye");
            reset();
        }
    }
}

fn list() {
    for i in COMMANDS{
        println!("{}\r\n",i.0);
    }
}

fn run_command(ctx: &mut Ctx) {
    let data = ctx.cons.as_str();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        for (name, imp) in COMMANDS {
            if *name == cmd {
                println!("\r\n");
                imp(ctx);
                return;
            }
        }
        println!("\r\nCommand not found,   \"{}\" try from > \r\n \r\n", &cmd);
        list();
    }
}

type Command = fn(&mut Ctx);

static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("r", cmd_other),
    ("help", cmd_help),
    ("?", cmd_help),
    ("demo", cmd_demo),
    ("clear", cmd_cls),
    ("reset", cmd_reset),
    ("+", cmd_add),
    ("-", cmd_sub),
];

fn cmd_add(ctx: &mut Ctx) {
    ctx.counter += 10;
}
fn cmd_sub(ctx: &mut Ctx) {
    if ctx.counter > 11 {
        ctx.counter -= 10;
    }
}

fn cmd_cls(ctx: &mut Ctx) {
    ctx.cons.clear_screen();
}

fn cmd_demo(_ctx: &mut Ctx) {
    println!("demo WOO HOO!");
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}

fn cmd_other(ctx: &mut Ctx) {
    terminal::rectangle(ctx.counter, 10);
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}

fn cmd_help(_ctx: &mut Ctx) {
    println!("Available commands\r\n\r\n");
    list();
    println!("\r\nThis is a simple readline for hapenny\r\n");
}
