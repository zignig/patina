#![no_std]
#![no_main]

use rustv::init::{reset, wait};
use rustv::readline;
//use rustv::terminal;
use rustv::uart::{write,writer};

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
    let intro = "Welcome to patina";
    write("\r\n\r\n");
    writer(intro);
    write(PROMPT);

    let mut counter: u32 = 0;
    let mut ctx = Ctx::new();
    loop {
        use readline::ConsoleAction::*;
        // get sometihng from the serial port
        if let Some(val) = ctx.cons.process() {
            {
                match val {
                    Tab => {
                        // println!("\r\n");
                        // println!("Commands: \r\n");
                        // list();
                        ctx.cons.redraw_line();
                        // ctx.cons.redraw();
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
                        writer("");
                        write(PROMPT);
                    }
                    _ => write(val.show()),
                }
                // Stuff happened.
                counter = 0;
            }
        }
        // bug out timer
        counter = counter + 1;
        if counter > 6000_000_0 {
            write("bye");
            reset();
        }
    }
}

fn list() {
    for i in COMMANDS {
        writer(i.0);
    }
}

fn run_command(ctx: &mut Ctx) {
    let data = ctx.cons.as_str();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        for (name, imp) in COMMANDS {
            if *name == cmd {
                write("\r\n");
                imp(ctx);
                return;
            }
        }
        write("\r\nCommand not found,\"{}\" try from > \r\n \r\n");
        write(&cmd);
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
    write("demo WOO HOO!");
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}

fn cmd_other(_ctx: &mut Ctx) {
    write("other");
    //terminal::rectangle(ctx.counter, 10);
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}

fn cmd_help(_ctx: &mut Ctx) {
    write("Available commands\r\n\r\n");
    list();
    write("\r\nThis is a simple readline for hapenny\r\n");
}
