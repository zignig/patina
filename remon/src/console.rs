//! Serial console
//!
//! brazenly stolen from https://github.com/dhylands/serial-monitor (well, some bits)
//!

use bytes::Bytes;
use std::time::Duration;

use futures::{future::FutureExt, select, StreamExt};
use futures_timer::Delay;
use tokio_serial::SerialPort;

use crossterm::{
    cursor::position,
    event::{Event, EventStream, KeyCode, KeyEvent, KeyModifiers},
    terminal::{disable_raw_mode, enable_raw_mode},
};

use crate::BootTool;

pub enum ProgramError {
    NoPortFound,
}

pub type Result<T> = std::result::Result<T, ProgramError>;

// Converts key events from crossterm into appropriate character/escape sequences which are then
// sent over the serial connection.
fn handle_key_event(key_event: KeyEvent) -> Result<Option<Bytes>> {
    // The following escape sequeces come from the MicroPython codebase.
    //
    //  Up      ESC [A
    //  Down    ESC [B
    //  Right   ESC [C
    //  Left    ESC [D
    //  Home    ESC [H  or ESC [1~
    //  End     ESC [F  or ESC [4~
    //  Del     ESC [3~
    //  Insert  ESC [2~

    let mut buf = [0; 4];

    let key_str: Option<&[u8]> = match key_event.code {
        KeyCode::Backspace => Some(b"\x08"),
        KeyCode::Left => Some(b"\x1b[D"),
        KeyCode::Right => Some(b"\x1b[C"),
        KeyCode::Home => Some(b"\x1b[H"),
        KeyCode::End => Some(b"\x1b[F"),
        KeyCode::Up => Some(b"\x1b[A"),
        KeyCode::Down => Some(b"\x1b[B"),
        KeyCode::Tab => Some(b"\x09"),
        KeyCode::Delete => Some(b"\x1b[3~"),
        KeyCode::Insert => Some(b"\x1b[2~"),
        KeyCode::Esc => Some(b"\x1b"),
        KeyCode::Char(ch) => {
            if key_event.modifiers & KeyModifiers::CONTROL == KeyModifiers::CONTROL {
                buf[0] = ch as u8;
                if (ch >= 'a' && ch <= 'z') || (ch == ' ') {
                    buf[0] &= 0x1f;
                    Some(&buf[0..1])
                } else if ch >= '4' && ch <= '7' {
                    // crossterm returns Control-4 thru 7 for \x1c thru \x1f
                    buf[0] = (buf[0] + 8) & 0x1f;
                    Some(&buf[0..1])
                } else {
                    Some(ch.encode_utf8(&mut buf).as_bytes())
                }
            } else {
                Some(ch.encode_utf8(&mut buf).as_bytes())
            }
        }
        _ => None,
    };
    if let Some(key_str) = key_str {
        Ok(Some(Bytes::copy_from_slice(key_str)))
    } else {
        Ok(None)
    }
}

async fn print_events(_port: &mut Box<dyn SerialPort>, debug: bool) {
    let mut reader = EventStream::new();
    //let (rx_port, tx_port) = tokio::io::split(port);

    loop {
        let mut delay = Delay::new(Duration::from_millis(1_000)).fuse();
        let mut event = reader.next().fuse();

        select! {
            _ = delay => { println!(".\r"); },
            maybe_event = event => {
                match maybe_event {
                    Some(Ok(event)) => {
                        if debug {
                            println!("Event::{:?}\r", event);
                        }
                        //let k = handle_key_event(event);
                        //println!("{k}");
                        if event == Event::Key(KeyEvent::new(KeyCode::Char('5'), KeyModifiers::CONTROL)) {
                            break;
                        }
                        if event == Event::Key(KeyCode::Char('c').into()) {
                            println!("Cursor position: {:?}\r", position());
                        }
                    }
                    Some(Err(e)) => println!("Error: {:?}\r", e),
                    None => break,
                }
            }
        };
    }
}

pub async fn run_console(port: &mut Box<dyn SerialPort>, debug: bool) -> std::io::Result<()> {
    enable_raw_mode()?;
    print_events(port,debug).await;
    disable_raw_mode()
}
