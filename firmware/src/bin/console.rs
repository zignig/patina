#![no_std]
#![no_main]
#![deny(missing_docs)]

//! riscv32i rust target.

use rustv::readline;

use patina_pac::{
    flash::Flash,
    generated,
    init::{heap_start, reset, wait},
    print, println,
    uart::{Bind, DefaultSerial},
    warmboot::Warm,
    watchdog::Watchdog,
};

const PROMPT: &str = ">>";

// Actual devices
/// Primary data construct
/// Add more to me and it is made available to commands
struct Ctx {
    cons: readline::Console,
    counter: usize,
    warm: Warm,
    //led: ActualLed,
    //input: ActualInput,
    flash: Flash,
    watchdog: Watchdog,
}

/// Make a clean context.
impl Ctx {
    fn new() -> Self {
        Self {
            cons: readline::Console::new(),
            counter: 10,
            warm: Warm::new(),
            // led: Led::new(),
            // input: Input::new(),
            flash: Flash::new(),
            watchdog: Watchdog::new(),
        }
    }
}

/// riscv32i console in pure rust
#[no_mangle]
pub extern "C" fn main() -> ! {
    // Delay
    wait(600);

    println!("Welcome to patina it's awesome");
    println!("press esc to return to bootloader");
    println!("{}", generated::DATE_STAMP);

    let mut _counter: u32 = 0;

    // Create the main context
    let mut ctx = Ctx::new();

    // Hello flash, why are you sleeping ?
    ctx.flash.wakeup();

    // Dump a block.
    //cmd_flash(&mut ctx);

    print!("{}", PROMPT);

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
                        println!("\n{}", PROMPT);
                    }
                    Escape => {
                        println!("EXIT");
                        reset();
                    }
                    Enter => {
                        run_command(&mut ctx);
                        ctx.cons.reset();
                        println!();
                        print!("{}", PROMPT);
                    }
                    _ => {}
                }
                // Stuff happened.
                // counter = 0;
            }
        }
        // bug out timer
        // counter += 1;
        // if counter > 120_000_000 {
        //     println!("bye");
        //     wait(100_000);
        //     reset();
        // }
    }
}

fn list() {
    for i in COMMANDS {
        println!("{}", i.0);
    }
    println!();
}

fn run_command(ctx: &mut Ctx) {
    let data = ctx.cons.as_str();
    if let Some(cmd) = data.split_ascii_whitespace().next() {
        for (name, imp) in COMMANDS {
            if *name == cmd {
                println!("");
                imp(ctx);
                return;
            }
        }
        println!("Command not found,\"{}\" try from >", &cmd);
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
    ("jdec", cmd_jedec),
    ("poke", cmd_watchdog),
    ("count", cmd_count),
    ("heap", cmd_heap),
    ("ansi", cmd_ansi),
];

fn cmd_ansi(ctx: &mut Ctx) {
    // https://gist.github.com/ConnerWill/d4b6c776b509add763e17f9f113fd25b
    // ansi testing
    print!("\x1b[2J");
    print!("\x1b[0;999H");
    print!("\x1b[6n");
    while let Some(ch) = ctx.cons.serial.tget() {
        if ch != b'\x1b' {
            print!("{}", ch as char);
        }
    }
    print!("\x1b[1;1H");
}
fn cmd_heap(_ctx: &mut Ctx) {
    println!("{}", heap_start() as u32);
}

fn cmd_count(ctx: &mut Ctx) {
    // This will turn it on and start the watch dog.
    ctx.watchdog.poke();
    let mut count: u32 = 0;
    loop {
        count += 1;
        println!("{}", ctx.watchdog.read());
        if count > 5000 {
            return;
        }
    }
}

fn cmd_watchdog(ctx: &mut Ctx) {
    ctx.watchdog.poke();
}

fn cmd_flash(ctx: &mut Ctx) {
    for data in ctx.flash.read_iter(0x50000, 1290) {
        print!("{:02x}", data);
    }
    println!();
}

fn cmd_jedec(ctx: &mut Ctx) {
    let jd = ctx.flash.read_jedec();
    print!("{:?}", jd);
}

fn cmd_rect(_ctx: &mut Ctx) {
    //rectangle(ctx.counter, ctx.counter);
    //show_boxen();
}

fn cmd_read(ctx: &mut Ctx) {
    loop {
        // let val: u16 = ctx.input.read();
        if let Some(_c) = ctx.cons.serial.get() {
            return;
        }
        wait(10000);
    }
}

fn cmd_on(_ctx: &mut Ctx) {
    // ctx.led.on();
}

fn cmd_off(_ctx: &mut Ctx) {
    // ctx.led.off();
}

fn cmd_blink(_ctx: &mut Ctx) {
    const DELAY: u32 = 50_000;
    for _ in 0..10 {
        wait(DELAY);
        // ctx.led.on();
        wait(DELAY);
        // ctx.led.off();
        print!("#");
    }
    println!();
}

fn cmd_warm(ctx: &mut Ctx) {
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
        println!();
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
    println!();
    println!("This is a simple readline for hapenny");
    println!("Available commands");
    list();
}
