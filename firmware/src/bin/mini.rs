#![no_std]
#![no_main]

use rustv::{
    flash::Flash,
    generated,
    init::{reset, wait},
    println, readline,
};

use patina_pac::{input::Input, led::Led, warmboot::Warmboot};

use rustv::uart::{Bind, DefaultSerial};

const PROMPT: &str = "|>";

// Actual devices
pub type ActualWarm = Warmboot<{ crate::generated::WARMBOOT_ADDR }>;

// Primary data construct
// Add more to me and it is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: usize,
    warm: ActualWarm,
}

impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 10,
            warm: Warmboot::new(),
            //input: Input::new(),
        }
    }
}

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(600);
    println!("Welcome to patina\r\n");
    println!("press esc to return to bootloader\r\n\r\n");
    println!("{}\r\n", generated::DATE_STAMP);
    println!("{}", PROMPT);

    let mut counter: u32 = 0;
    // Create the main context
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
                    Escape => {
                        println!("EXIT");
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
        counter += 1;
        if counter > 60_000_000 {
            println!("bye");
            wait(100_000);
            reset();
        }
    }
}

fn list() {
    for i in COMMANDS {
        println!("{} ", i.0);
    }
    println!("\r\n");
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

static COMMANDS: &[(&str, Command)] = &[("reset", cmd_reset), ("warm", cmd_warm)];

fn cmd_warm(ctx: &mut Ctx) {
    println!("0x{:x}", ctx.warm.addr());
    // wait for the the chars to spool out before rebooting
    wait(10000);
    ctx.warm.write();
}

fn cmd_reset(_ctx: &mut Ctx) {
    reset();
}
