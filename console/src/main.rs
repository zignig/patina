// Interact with a serial console device 
use std::{time::Duration, path::PathBuf, io::ErrorKind, io::Write};

use anyhow::{Context, Result, bail};
use indicatif::ProgressBar;
//use serialport::SerialPort;
use clap::Parser;

#[derive(Debug, Parser)]
#[clap(version)]
struct BootTool {
    /// Path to serial port on your machine, e.g. /dev/ttyUSB0 or COM1:
    port: String,
    /// Baud rate of serial port.
    #[clap(long, short, global = true, default_value_t = 115_200)]
    baud_rate: u32,

    #[clap(subcommand)]
    cmd: SubCmd,
}

#[derive(Debug, Parser)]
enum SubCmd {
    /// Perform a basic check to see if tinyboot appears to be running.
    Ping,
    /// Load a qsingle 32-bit word from an address in the target.
    Peek {
        /// Address to read.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
    },
    /// Write a single 32-bit word into the taget.
    Poke {
        /// Address to write.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
        /// Value to write.
        #[clap(value_parser = parse_int::parse::<u32>)]
        value: u32,
    },
    /// Write the contents of a file into the target. Useful for loading a
    /// program from a .bin file.
    Write {
        /// Address to begin writing.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
        /// File containing bytes to write; will be padded out to a multiple of
        /// 4.
        image_file: PathBuf,
    },
    /// Call into an address in the target.
    Call {
        /// Address to call.
        #[clap(value_parser = parse_int::parse::<u32>)]
        address: u32,
        /// If provided, the tool will immediately begin echoing back data
        /// received on the serial report until you kill it. This is useful for
        /// loading and running programs that are chatty, such as Dhrystone.
        #[clap(long)]
        then_echo: bool,
    },
}

fn main() -> Result<()> {
    let args = BootTool::parse();
    Ok(())
}
