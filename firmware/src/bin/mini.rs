#![no_std]
#![no_main]

use rustv::init::{reset, wait};
use rustv::{generated, println};
use rustv::readline;
//use rustv::terminal;
use rustv::uart::{Bind, DefaultSerial};
use rustv::warmboot::{ActualWarm,Warmboot};

const PROMPT: &str = ">";

// Primary data construct
// Add more to me and it is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: usize,
    warm: ActualWarm
}

impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 10,
            warm: Warmboot::new()
        }
    }
}

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(600);
    let intro = "Welcome to patina";
    println!("{}\r\n", intro);
    println!("{}\r\n",generated::DATE_STAMP);
    println!("{}", PROMPT);

    let mut counter: u32 = 0;
    let mut ctx = Ctx::new();
    loop {
        use readline::ConsoleAction::*;
        // get something from the serial port
        if let Some(val) = ctx.cons.process() {
            {
                match val {
                    Tab => {
                        ctx.cons.redraw_line();
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
                        println!("\n{}", PROMPT);
                    }
                    _ => println!("|{:?}", val),
                }
                // Stuff happened.
                counter = 0;
            }
        }
        // bug out timer
        counter = counter + 1;
        if counter > 6_000_000 {
            println!("bye");
            reset();
        }
    }
}

fn list() {
    for i in COMMANDS {
        println!(" -  {}\r\n", i.0);
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
        println!("\r\nCommand not found,\"{}\" try from > \r\n \r\n", &cmd);
        list();
    }
}

type Command = fn(&mut Ctx);

static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("help", cmd_help),
    ("?", cmd_help),
    ("demo", cmd_demo),
    ("clear", cmd_cls),
    ("reset", cmd_reset),
    ("+", cmd_add),
    ("-", cmd_sub),
    ("warm", cmd_warm)
];

fn cmd_warm(ctx: &mut Ctx) {
    println!("0x{:x}",ctx.warm.addr());
    // wait for the the chars to spool out before rebooting
    wait(10000);
    ctx.warm.write();
}

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

fn cmd_demo(ctx: &mut Ctx) {
    let mut counter: u32 = 16;
    while counter > 0 {
        for char in 32..126 {
            ctx.cons.serial.putb(char)
        }
        println!("\r\n");
        counter -= 1;
    }
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}


fn cmd_list(_ctx: &mut Ctx) {
    list();
}

fn cmd_help(_ctx: &mut Ctx) {
    println!("Available commands\r\n\r\n");
    list();
    println!("\r\nThis is a simple readline for hapenny\r\n");
}
