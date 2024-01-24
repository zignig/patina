use std::{path::PathBuf, time::Duration};

use anyhow::{Context, Result};
use clap::Parser;

mod cli;
mod console;

use cli::{do_call, do_cmd, do_peek, do_poke, do_write, drain};
use console::run_console;

//use console::traffic;

/// A tool for interacting with the hapenny tinyboot serial monitor.
#[derive(Debug, Parser)]
#[clap(version)]
struct BootTool {
    /// Path to serial port on your machine, e.g. /dev/ttyUSB0 or COM1:
    port: String,
    /// Baud rate of serial port.
    #[clap(long, short, global = true, default_value_t = 115_200)]
    baud_rate: u32,

    /// Attach to a serial console
    #[clap(long, short, global = true)]
    console: bool,
    /// Debug logging
    #[clap(long, short, global = true,default_value_t=false)]
    debug: bool,
    

    #[clap(subcommand)]
    cmd: Option<SubCmd>,
}

#[derive(Debug, Parser)]
enum SubCmd {
    /// Perform a basic check to see if tinyboot appears to be running.
    Ping,
    /// Load a single 32-bit word from an address in the target.
    Peek {
        /// Address to read.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
    },
    /// Write a single 32-bit word into the taget.
    Poke {
        /// Value to write.
        #[clap(value_parser = parse_int::parse::<u32>)]
        value: u32,
        /// Address to write.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
    },
    /// Write the contents of a file into the target. Useful for loading a
    /// program from a .bin file.
    Write {
        /// File containing bytes to write; will be padded out to a multiple of
        /// 4.
        image_file: PathBuf,
        /// Address to begin writing.
        #[clap(value_parser = parse_int::parse::<u32>,default_value_t = 0)]
        address: u32,
    },
    /// Call into an address in the target.
    Call {
        /// If provided, the tool will immediately begin echoing back data
        /// received on the serial report until you kill it. This is useful for
        /// loading and running programs that are chatty, such as Dhrystone.
        #[clap(long)]
        then_echo: bool,
        /// Address to call.
        #[clap(value_parser = parse_int::parse::<u32>,default_value_t = 0)]
        address: u32,
    },
    /// Write and then Call at the given address , (default zero).
    Run {
        /// File containing bytes to write; will be padded out to a multiple of
        /// 4.
        image_file: PathBuf,
        #[clap(value_parser = parse_int::parse::<u32>,default_value_t = 0)]
        address: u32,
        #[clap(long)]
        then_echo: bool,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = BootTool::parse();

    let mut port = tokio_serial::new(&args.port, args.baud_rate)
        .timeout(Duration::from_millis(500))
        .open()
        .with_context(|| format!("opening serial port {}", args.port))?;

    if let Some(cmd) = args.cmd {
        drain(&mut port)?;
        match cmd {
            SubCmd::Ping => {
                do_cmd(&mut port, &[5]).context("pinging")?;
            }

            SubCmd::Peek { address } => {
                do_peek(address, &mut port)?;
            }

            SubCmd::Poke { address, value } => {
                do_poke(address, value, &mut port)?;
            }

            SubCmd::Write {
                address,
                image_file,
            } => {
                do_write(image_file, address, &mut port)?;
            }

            SubCmd::Call { address, then_echo } => {
                do_call(address, &mut port, then_echo)?;
            }

            SubCmd::Run {
                address,
                image_file,
                then_echo,
            } => {
                do_write(image_file, address, &mut port)?;
                do_call(address, &mut port, then_echo)?;
            }
        }
    }
    if args.console {
        println!("^] to exit.");
        run_console(&mut port,args.debug).await?;
    }

    Ok(())
}
