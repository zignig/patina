//! Demonstrates how to read events asynchronously with tokio.
//!
//! cargo run --features="event-stream" --example event-stream-tokio

use std::time::Duration;

use futures::{future::FutureExt, select, StreamExt};
use futures_timer::Delay;
use tokio_serial::SerialPort;

use crossterm::{
    cursor::position,
    event::{Event, EventStream, KeyCode, KeyEvent, KeyModifiers},
    terminal::{disable_raw_mode, enable_raw_mode},
};

async fn print_events() {
    let mut reader = EventStream::new();

    loop {
        let mut delay = Delay::new(Duration::from_millis(1_000)).fuse();
        let mut event = reader.next().fuse();

        select! {
            _ = delay => { println!(".\r"); },
            maybe_event = event => {
                match maybe_event {
                    Some(Ok(event)) => {
                        println!("Event::{:?}\r", event);
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

pub async fn run_console(_port: &mut Box<dyn SerialPort>) -> std::io::Result<()> {
    enable_raw_mode()?;
    print_events().await;
    disable_raw_mode()
}
