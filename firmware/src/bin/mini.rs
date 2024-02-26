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

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(60000);
    let intro = "Welcome to new patina";
    println!("{}\r\n\r\n", intro);
    println!("{}", PROMPT);
    let mut cons: readline::Console<{ crate::generated::UART_ADDR }> = readline::Console::new();
    let mut counter: u32 = 0;
    loop {
        if let Some(val) = cons.process() {
            {
                counter = 0;
                match val {
                    readline::ConsoleAction::Char(c) => println!("{}", (c as char)),
                    // readline::ConsoleAction::Up => todo!(),
                    // readline::ConsoleAction::Down => todo!(),
                    // readline::ConsoleAction::Left => todo!(),
                    // readline::ConsoleAction::Right => todo!(),
                    // readline::ConsoleAction::Home => todo!(),
                    // readline::ConsoleAction::End => todo!(),
                    // readline::ConsoleAction::Insert => todo!(),
                    // readline::ConsoleAction::Delete => todo!(),
                    // readline::ConsoleAction::PgUp => todo!(),
                    // readline::ConsoleAction::PgDown => todo!(),
                    // readline::ConsoleAction::Escape => todo!(),
                    readline::ConsoleAction::Tab => {
                        println!("\r\n");
                        println!("Commands: \r\n");
                        list();
                    }
                    // readline::ConsoleAction::Cancel => todo!(),
                    // readline::ConsoleAction::Reset => todo!(),
                    readline::ConsoleAction::Enter => {
                        let data = cons.as_str();
                        run_command(data);
                        cons.reset();
                        println!("\r\n{}", PROMPT);
                    }
                    // readline::ConsoleAction::BackSpace => todo!(),
                    _ => println!("_{:?}_", val),
                }
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
        println!("{}> {}\r\n", i, *COMMANDS[i].0);
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
    ("other", cmd_other),
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

fn cmd_other(_ctx: &mut Ctx) {
    println!("the other command");
}

fn cmd_list(_ctx: &mut Ctx) {
    list();
}

fn cmd_help(_ctx: &mut Ctx) {
    println!("This is some unhelpful help\r\n stuff\r\n stuff.\r\n");
}
