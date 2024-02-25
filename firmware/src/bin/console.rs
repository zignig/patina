#![no_std]
#![no_main]

use rustv::init::{reset, wait};
use rustv::println;
use rustv::uart::{Bind, DefaultSerial};

use rustv::readline;

// Default reset from build system (.cargo/config.toml)
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

const PROMPT: &str = ">>";

#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(60000);
    let intro = "Welcome to new patina";
    println!("{}\r\n", intro);
    println!("{}", PROMPT);
    let mut console: readline::Console<{ generated::UART_ADDR }> = readline::Console::new();

    loop {
        if let Some(comm) = console.read_key_board() {
            println!("{:?}",comm);
            match comm {
                readline::ConsoleAction::Char(c) => console.serial.putb(c),
                readline::ConsoleAction::Up => println!("UP"),
                readline::ConsoleAction::Down => todo!(),
                readline::ConsoleAction::Left => todo!(),
                readline::ConsoleAction::Right => todo!(),
                readline::ConsoleAction::Home => todo!(),
                readline::ConsoleAction::Insert => todo!(),
                readline::ConsoleAction::Delete => todo!(),
                readline::ConsoleAction::PgUp => todo!(),
                readline::ConsoleAction::PgDown => todo!(),
                readline::ConsoleAction::Escape => todo!(),
                readline::ConsoleAction::Tab => todo!(),
                readline::ConsoleAction::Cancel => todo!(),
                readline::ConsoleAction::Reset => reset(),
                readline::ConsoleAction::Enter => todo!(),
                readline::ConsoleAction::BackSpace => todo!(),
                readline::ConsoleAction::End => todo!(),
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
