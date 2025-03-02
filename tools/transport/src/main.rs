use anyhow::{bail, Context, Result};
use clap::Parser;
use indicatif::ProgressBar;
use serialport;
use std::{io::ErrorKind, io::Write, path::PathBuf, time::Duration};

mod upload;

/// A tool for interacting with the hapenny tinyboot serial monitor.
#[derive(Debug, Parser)]
#[clap(version)]
struct TransportTool {
    /// Path to serial port on your machine, e.g. /dev/ttyUSB0 or COM1:
    #[clap(long, short, global = true, default_value_t = {"/dev/ttyUSB0".to_string()})]
    port: String,
    /// Baud rate of serial port.
    #[clap(long, short, global = true, default_value_t = 115_200)]
    baud_rate: u32,
    // #[clap(subcommand)]
    // cmd: SubCmd,
}

fn main() -> Result<()> {
    let args = TransportTool::parse();
    println!("{:#?}", args);
    let port = serialport::new(&args.port, args.baud_rate)
        .timeout(Duration::from_millis(500))
        .open()
        .with_context(|| format!("opening serial port {}", args.port))?;
    args.
    println!("{:#?}", &port);

    Ok(())
}
