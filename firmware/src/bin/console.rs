#![no_std]
#![no_main]

#![deny(missing_docs)]

//! riscv32i rust target.

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
/// Flash connected to the board ( uses spi.py interface)
pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;
/// Single led on the tinybox board
pub type ActualLed = Led<{ generated::OUTPUTPORT_ADDR }>;
/// Input pind
pub type ActualInput = Input<{ crate::generated::INPUTPORT_ADDR }>;
/// Internal warmboot device on the ice40
pub type ActualWarm = Warmboot<{ crate::generated::WARMBOOT_ADDR }>;

// Primary data construct
// Add more to me and it is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: usize,
    warm: ActualWarm,
    led: ActualLed,
    input: ActualInput,
    flash: TinyFlash,
}

impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 10,
            warm: Warmboot::new(),
            led: Led::new(),
            input: Input::new(),
            flash: Flash::new(),
        }
    }
}

/// riscv32i console in pure rust
#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(600);
    println!("Welcome to patina\r\n");
    println!("press esc to return to bootloader\r\n\r\n");
    println!("{}\r\n", generated::DATE_STAMP);
    

    let mut counter: u32 = 0;
    // Create the main context
    let mut ctx = Ctx::new();

    ctx.led.on();
    wait(10000);
    ctx.led.off();

    ctx.flash.wakeup();
    // ctx.flash.read_block(0x50000, 1290);
    println!("{}", PROMPT);
    cmd_flash(&mut ctx);

    loop {
        // get something from the serial port
        if let Some(val) = ctx.cons.process() {
            // Take a console event
            use readline::ConsoleAction::*;
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

static COMMANDS: &[(&str, Command)] = &[
    ("list", cmd_list),
    ("help", cmd_help),
    ("?", cmd_help),
    ("demo", cmd_demo),
    ("clear", cmd_cls),
    ("reset", cmd_reset),
    ("+", cmd_add),
    ("-", cmd_sub),
    ("warm", cmd_warm),
    ("on", cmd_on),
    ("off", cmd_off),
    ("blink", cmd_blink),
    ("read", cmd_read),
    ("rect", cmd_rect),
    ("fl", cmd_flash),
    ("jdec",cmd_jedec)
];

fn cmd_flash(ctx: &mut Ctx) {
    ctx.flash.read_block(0x50000, 1290);
    //let addr = 0;
    // for i in 0..50{
    //     ctx.flash.read_block(i*2048, 2048);
    // }
}

fn cmd_jedec(ctx: &mut Ctx) {
    let jd = ctx.flash.read_jedec();
    println!("{:?}",jd);
}

fn cmd_rect(_ctx: &mut Ctx) {
    //rectangle(ctx.counter, ctx.counter);
    //show_boxen();
}

fn cmd_read(ctx: &mut Ctx) {
    loop {
        let val: u16 = ctx.input.read();
        if let Some(_c) = ctx.cons.serial.get() {
            return;
        }
        println!("{}", val);
        wait(10000);
    }
}

fn cmd_on(ctx: &mut Ctx) {
    ctx.led.on();
}

fn cmd_off(ctx: &mut Ctx) {
    ctx.led.off();
}

fn cmd_blink(ctx: &mut Ctx) {
    const DELAY: u32 = 50_000;
    for _ in 0..10 {
        wait(DELAY);
        ctx.led.on();
        wait(DELAY);
        ctx.led.off();
        println!("#");
    }
}

fn cmd_warm(ctx: &mut Ctx) {
    println!("0x{:x}", ctx.warm.addr());
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
    println!("\r\nThis is a simple readline for hapenny\r\n\r\n");
    println!("Available commands\r\n\r\n");
    list();
}
