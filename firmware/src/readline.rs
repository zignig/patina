//! Reader and decoder for an ANSI terminal.

use heapless::String;
use patina_pac::{println,print};
use patina_pac::uart::{Bind, DefaultSerial};
// use ufmt::derive::uDebug;

const PROMPT: &str = ">>";

/// An enumeration of actions that come from the console
// #[derive(uDebug)]
pub enum ConsoleAction {
    /// Single Char
    Char(u8),
    /// Up cursor key
    Up,
    /// Down cursor
    Down,
    /// Left key
    Left,
    /// Right key
    Right,
    /// Home key
    Home,
    /// End key
    End,
    /// Insert key
    Insert,
    /// Delete key
    Delete,
    /// Page up key
    PgUp,
    /// Page down key
    PgDown,
    /// Escape key by itself
    Escape,
    /// Tab Key
    Tab,
    /// Control C
    Cancel,
    /// Control D
    Reset,
    /// Enter Key
    Enter,
    /// Back space
    BackSpace,
    /// Control Z
    CtlZ,
    /// Unknown key strokes
    Unknown,
}

const BUF_SIZE: usize = 64;

#[derive(Clone)]
struct Buffer {
    data: String<BUF_SIZE>,
    cursor: usize,
}

impl Buffer {
    fn new() -> Self {
        Self {
            data: String::new(),
            cursor: 0,
        }
    }

    fn reset(&mut self) {
        self.data.clear();
        self.cursor = 0;
    }

    // fn insert(&mut self, _c: char) {}
    fn push_str(&mut self, s: &str) {
        self.data.push_str(s).unwrap();
    }
}

impl Default for Console {
    fn default() -> Self {
        Self::new()
    }
}

/// Struct for the console
pub struct Console {
    buffer: Buffer,
    /// point to the serial device
    pub serial: patina_pac::uart::DefaultSerial, //pub serial: crate::uart::Serial<ADDR>,
    //insert: bool,
    echo: bool,
}

impl Console {
    /// Create a new console
    pub fn new() -> Self {
        Self {
            buffer: Buffer::new(),
            serial: DefaultSerial::new(),
            // insert: true,
            echo: true,
        }
    }

    /// Return the buffer as a string
    pub fn as_str(&mut self) -> &str {
        return self.buffer.data.as_str();
    }

    /// Reset the buffer
    pub fn reset(&mut self) {
        self.buffer.reset();
    }

    /// Process a key stroke
    pub fn process(&mut self) -> Option<ConsoleAction> {
        if let Some(act) = self.read_key_board() {
            match act {
                ConsoleAction::Char(c) => {
                    if self.echo {
                        print!("{}", (c as char));
                    }
                    None
                }

                // Perhaps a history ?
                ConsoleAction::Up => {
                    self.reply(act);
                    None
                }
                ConsoleAction::Down => { 
                    self.reply(act);
                    None
                }
                //ConsoleAction::Down => None,
                ConsoleAction::Left => {
                    if self.buffer.cursor > 0 {
                        self.buffer.cursor -= 1;
                        self.reply(act);
                    }
                    None
                }
                ConsoleAction::Right => {
                    if self.buffer.cursor < self.buffer.data.len() {
                        self.buffer.cursor += 1;
                        self.reply(act);
                    }
                    None
                }
                // ConsoleAction::Home => todo!(),
                // ConsoleAction::End => todo!(),
                //ConsoleAction::Insert => todo!(),
                // ConsoleAction::Delete => todo!(),

                // What to do with these ?
                //ConsoleAction::PgUp => None,
                //ConsoleAction::PgDown => None,

                // ConsoleAction::Escape => todo!(),
                // ConsoleAction::Tab => todo!(),
                // ConsoleAction::Cancel => todo!(),
                // ConsoleAction::Reset => todo!(),
                ConsoleAction::Enter => {
                    // Bubble up the enter
                    Some(act)
                }
                ConsoleAction::BackSpace => {
                    // self.backspace();
                    None
                }

                // If none of these are grabbed , bubble up.
                _ => Some(act),
            }
        } else {
            None
        }
    }

    /// Send some chars back to the attched console
    pub fn reply(&mut self, action: ConsoleAction) {
        if let Some(val) = match action {
            // ConsoleAction::Char(_) => todo!(),
            ConsoleAction::Up => Some("\x1b\x5b\x41"),
            ConsoleAction::Down => Some("\x1b\x5b\x42"),
            // ConsoleAction::Down => todo!(),
            ConsoleAction::Left => Some("\x1b\x5b\x44"),
            ConsoleAction::Right => Some("\x1b\x5b\x43"),
            // ConsoleAction::Home => todo!(),
            // ConsoleAction::End => todo!(),
            // ConsoleAction::Insert => todo!(),
            // ConsoleAction::Delete => todo!(),
            // ConsoleAction::PgUp => todo!(),
            // ConsoleAction::PgDown => todo!(),
            // ConsoleAction::Escape => todo!(),
            // ConsoleAction::Tab => todo!(),
            // ConsoleAction::Cancel => todo!(),
            // ConsoleAction::Reset => todo!(),
            // ConsoleAction::Enter => todo!(),
            // ConsoleAction::BackSpace => todo!(),
            _ => None,
        } {
            print!("{}", val);
        }
    }

    /// Process backspce key
    pub fn backspace(&mut self) {
        let _ = self.buffer.data.remove(self.buffer.cursor);
        self.redraw_line();
    }

    /// Split the buffer into words
    pub fn split_list(&mut self) {
        // this is unsafe beacuse the full split uses the full unicode libs
        // and the firmware blows out by 7Kb.
        unsafe {
            let buf = &self.buffer.clone();
            let start = buf.data.get_unchecked(0..buf.cursor - 1);
            let end = buf.data.get_unchecked(buf.cursor..buf.data.len());

            println!("{}|{}", start, end);
            self.buffer.reset();
            self.buffer.push_str(start);
            //self.buffer.push('|');
            self.buffer.push_str(end);
        }
    }

    /// Clear and redraw the current buffer
    pub fn redraw_line(&mut self) {
        //Clear line
        print!("\x1b[2K");
        // Move al the way left
        print!("\x1b[G");
        print!("{}", PROMPT);
        print!("{}", self.buffer.data.as_str());
    }

    /// Clean the entire screen
    pub fn clear_screen(&mut self) {
        print!("\x1b[2J\x1b[H"); // clear screen and home
    }

    /// Process a keystroke(s)
    pub fn read_key_board(&mut self) -> Option<ConsoleAction> {
        if let Some(c) = self.serial.get() {
            match c {
                b'\x03' => {
                    // Control C
                    return Some(ConsoleAction::Cancel);
                }
                b'\x04' => {
                    // Control D
                    return Some(ConsoleAction::Reset);
                }
                b'\x09' => {
                    return Some(ConsoleAction::Tab);
                }
                b'\x0A' => {
                    // Enter
                    return Some(ConsoleAction::Enter);
                }
                b'\x7f' => {
                    // Backspace
                    return Some(ConsoleAction::BackSpace);
                }
                // \x1b
                b'\x1b' => {
                    // cursor keys
                    if let Some(c) = self.serial.tget() {
                        match c {
                            b'\x5b' => {
                                if let Some(c) = self.serial.tget() {
                                    match c {
                                        b'\x41' => {
                                            return Some(ConsoleAction::Up);
                                        }
                                        b'\x42' => {
                                            return Some(ConsoleAction::Down);
                                        }
                                        b'\x43' => {
                                            return Some(ConsoleAction::Right);
                                        }
                                        b'\x44' => {
                                            return Some(ConsoleAction::Left);
                                        }
                                        b'\x31' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::Home);
                                            }
                                        }
                                        b'\x32' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::Insert);
                                            }
                                        }
                                        b'\x33' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::Delete);
                                            }
                                        }
                                        b'\x34' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::End);
                                            }
                                        }
                                        b'\x35' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::PgUp);
                                            }
                                        }
                                        b'\x36' => {
                                            if self.serial.tget().is_some() {
                                                return Some(ConsoleAction::PgDown);
                                            }
                                        }

                                        _ => {
                                            return Some(ConsoleAction::Unknown);
                                        }
                                    }
                                }
                            }
                            _ => {
                                return Some(ConsoleAction::Unknown);
                            }
                        }
                    } else {
                        return Some(ConsoleAction::Escape);
                    }
                }
                _ => {
                    //self.serial.putb(c);
                    let _ = self.buffer.data.push(c as char);
                    self.buffer.cursor += 1;
                    return Some(ConsoleAction::Char(c));
                }
            }
        }
        None
    }
}
