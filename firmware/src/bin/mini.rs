#![no_std]
#![no_main]

use rustv::init::{reset, wait};
use rustv::println;
use rustv::readline;
use rustv::uart::{Bind, DefaultSerial};



const PROMPT: &str = ">>";

// Default reset from build system (.cargo/config.toml)
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

// Primary data construct
// Add more to me is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: u32,
}


impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 0,
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
                    // Char(_) => todo!(),
                    // Up => todo!(),
                    // Down => todo!(),
                    // Left => todo!(),
                    // Right => todo!(),
                    // Home => todo!(),
                    // End => todo!(),
                    // Insert => todo!(),
                    // Delete => todo!(),
                    // PgUp => todo!(),
                    // PgDown => todo!(),
                    // Escape => todo!(),
                    Tab => {
                        println!("\r\n");
                        println!("Commands: \r\n");
                        list();
                    }
                    Cancel => {
                        ctx.cons.clear_screen();
                    }
                    //Reset => todo!(),
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
    let len = COMMANDS.len();
    for i in 0..len {
        println!("{}: {}\r\n", i, *COMMANDS[i].0);
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
        println!("\r\nCommand not found \"{}\"", &cmd);
    }
}

type Command = fn(&mut Ctx);

static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("info", cmd_empty),
    ("other", cmd_other),
    ("help", cmd_help),
    ("?", cmd_help),
    ("demo", cmd_demo),
    ("cls", cmd_cls),
    ("reset", cmd_reset),
    ("+", cmd_plus),
];

fn cmd_plus(ctx: &mut Ctx) {
    ctx.counter += 1;
    println!("{}", ctx.counter);
}

fn cmd_cls(ctx: &mut Ctx) {
    ctx.cons.clear_screen();
}

fn cmd_demo(_ctx: &mut Ctx) {
    println!("demo WOO HOO!");
}

fn cmd_empty(_ctx: &mut Ctx) {
    println!("empty command");
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}

fn cmd_other(_ctx: &mut Ctx) {
    println!("the other command");
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}

fn cmd_help(_ctx: &mut Ctx) {
    println!("Available commands\r\n\r\n");
    list();
    println!("\r\nThis is a simple readline for hapenny\r\n");
}
