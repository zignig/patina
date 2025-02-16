#![no_std]
#![no_main]
#![deny(missing_docs)]

//! riscv32i rust target.

use rustv::readline;

use patina_pac::{
    generated,
    init::{heap_start, reset, wait},
    println,
    uart::{Bind, DefaultSerial},
    warmboot::Warm,
    watchdog::Watchdog,
    flash::Flash,
};

const PROMPT: &str = "|>";

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

    println!("Welcome to patina it's awesome\r\n");
    println!("press esc to return to bootloader\r\n\r\n");
    println!("{}\r\n", generated::DATE_STAMP);

    let mut _counter: u32 = 0;

    // Create the main context
    let mut ctx = Ctx::new();

    // Hello flash, why are you sleeping ?
    ctx.flash.wakeup();

    // Dump a block.
    //cmd_flash(&mut ctx);

    println!("{}", PROMPT);

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
                        println!("\n{}", PROMPT);
                    }
                    _ => {} //println!("|{:?}", val),
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
        println!("{}\r\n", i.0);
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
    ("jdec", cmd_jedec),
    ("poke", cmd_watchdog),
    ("count", cmd_count),
    ("heap", cmd_heap),
];

fn cmd_heap(_ctx: &mut Ctx) {
    println!("{}", heap_start() as u32);
}

fn cmd_count(ctx: &mut Ctx) {
    // This will turn it on and start the watch dog.
    ctx.watchdog.poke();
    let mut count: u32 = 0;
    loop {
        //println!("{}\r\n", count);
        count += 1;
        println!("{}\r\n", ctx.watchdog.read());
        if count > 5000 {
            return;
        }
    }
}

fn cmd_watchdog(ctx: &mut Ctx) {
    ctx.watchdog.poke();
}

fn cmd_flash(ctx: &mut Ctx) {
    for data in ctx.flash.read_iter(0x50000, 1290){
        println!("{}",data);
    }
    println!("\r\n");
}

fn cmd_jedec(ctx: &mut Ctx) {
    let jd = ctx.flash.read_jedec();
    println!("{:?}", jd);
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
        // println!("{}", val);
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
