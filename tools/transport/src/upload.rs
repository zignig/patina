use std::{io::ErrorKind, io::Write, path::PathBuf, time::Duration};

use anyhow::{bail, Context, Result};
use clap::Parser;
use indicatif::ProgressBar;
use serialport::SerialPort;

pub fn do_write(
    image_file: PathBuf,
    address: u32,
    port: &mut Box<dyn SerialPort>,
) -> Result<(), anyhow::Error> {
    let mut image = std::fs::read(&image_file)?;
    while image.len() % 4 != 0 {
        image.push(0);
    }
    let mut cmd = [3, 0, 0, 0, 0];
    cmd[1..].copy_from_slice(&address.to_le_bytes());
    do_cmd(port, &cmd).context("loading A")?;
    let bar = ProgressBar::new(image.len() as u64);
    for chunk in image.chunks(256) {
        // load count register
        let word_count = u32::try_from(chunk.len() / 4)?;
        let mut cmd = [4, 0, 0, 0, 0];
        cmd[1..].copy_from_slice(&word_count.to_le_bytes());
        do_cmd(port, &cmd).context("loading C")?;
        let mut packet = vec![1];
        packet.extend_from_slice(chunk);
        // deposit the data.
        do_cmd(port, &packet).context("sending PUT")?;
        bar.inc(chunk.len() as u64);
    }
    bar.finish();
    Ok(())
}

pub fn do_call(
    address: u32,
    mut port: Box<dyn SerialPort>,
    then_echo: bool,
) -> Result<(), anyhow::Error> {
    let mut cmd = [3, 0, 0, 0, 0];
    cmd[1..].copy_from_slice(&address.to_le_bytes());
    do_cmd(&mut port, &cmd).context("loading A")?;
    do_cmd(&mut port, &[0]).context("sending CALL")?;
    Ok(if then_echo {
        let stdout = std::io::stdout();
        let mut stdout = stdout.lock();
        loop {
            let mut b = [0];
            match port.read_exact(&mut b) {
                Ok(()) => {
                    write!(stdout, "{}", b[0] as char)?;
                    stdout.flush()?;
                }
                Err(e) if e.kind() == ErrorKind::TimedOut => {
                    // meh
                }
                other => other?,
            }
        }
    })
}

pub fn do_cmd(port: &mut Box<dyn SerialPort>, cmd: &[u8]) -> Result<()> {
    port.write_all(&cmd).context("writing command")?;
    let mut response = [0; 1];
    port.read_exact(&mut response)
        .context("collecting response byte")?;
    match response[0] {
        0xAA => Ok(()),
        0xFF => {
            bail!("Received NACK");
        }
        x => {
            bail!("Received unexpected response: {x:#x}");
        }
    }
}

pub fn drain(port: &mut Box<dyn SerialPort>) -> Result<()> {
    let saved_timeout = port.timeout();

    port.set_timeout(Duration::from_millis(1))
        .context("reducing timeout for drain")?;

    let mut buffer = [0; 32];
    let mut cruft = 0_usize;
    loop {
        match port.read(&mut buffer) {
            Ok(n) => cruft += n,
            Err(e) if e.kind() == ErrorKind::TimedOut => {
                break;
            }
            Err(e) => return Err(e).context("attempting to drain buffer"),
        }
    }
    port.set_timeout(saved_timeout)
        .context("restoring timeout after drain")?;

    if cruft > 0 {
        println!("note: {cruft} bytes of cruft drained from serial port");
    }

    Ok(())
}
