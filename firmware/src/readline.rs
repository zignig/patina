use crate::uart::{write, write_char, Bind, DefaultSerial};
use heapless::String;
//use ufmt::derive::uDebug;

const PROMPT: &str = ">>";

//#[derive(uDebug)]
pub enum ConsoleAction {
    Char(u8),
    Up,
    Down,
    Left,
    Right,
    Home,
    End,
    Insert,
    Delete,
    PgUp,
    PgDown,
    Escape,
    Tab,
    Cancel,
    Reset,
    Enter,
    BackSpace,
    Unknown,
}

impl ConsoleAction {

    pub fn show(&self) -> &str {
        let val = match self{
            ConsoleAction::Char(_) => "Char",
            ConsoleAction::Up => "Up",
            ConsoleAction::Down => "Down",
            ConsoleAction::Left => "Left",
            ConsoleAction::Right => "Right",
            ConsoleAction::Home => "Home",
            ConsoleAction::End => "End",
            ConsoleAction::Insert => "Insert",
            ConsoleAction::Delete => "Delete",
            ConsoleAction::PgUp => "PgUp",
            ConsoleAction::PgDown => "PgDown",
            ConsoleAction::Escape => "Escape",
            ConsoleAction::Tab => "Tab",
            ConsoleAction::Cancel => "Cancel",
            ConsoleAction::Reset => "Reset",
            ConsoleAction::Enter => "Enter",
            ConsoleAction::BackSpace => "Backspace",
            ConsoleAction::Unknown => "Unknown",
        };
        val
    }
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

    // fn push(&mut self, c: char) {
    //     let _ = self.data.push(c);
    // }
}

pub struct Console {
    buffer: Buffer,
    serial: crate::uart::DefaultSerial, //pub serial: crate::uart::Serial<ADDR>,
    //insert: bool,
    echo: bool,
}

impl Console {
    pub fn new() -> Self {
        Self {
            buffer: Buffer::new(),
            serial: DefaultSerial::new(),
            // insert: true,
            echo: true,
        }
    }

    pub fn as_str(&mut self) -> &str {
        return self.buffer.data.as_str();
    }

    pub fn reset(&mut self) {
        self.buffer.reset();
    }

    pub fn process(&mut self) -> Option<ConsoleAction> {
        if let Some(act) = self.read_key_board() {
            match act {
                ConsoleAction::Char(c) => {
                    if self.echo {
                        write_char(c)
                    }
                    None
                }

                // Perhaps a history ?
                //ConsoleAction::Up => None,
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
                // ConsoleAction::Enter => todo!(),
                ConsoleAction::BackSpace => {
                    //self.backspace();
                    None
                }

                // If none of these are grabbed , bubble up.
                _ => Some(act),
            }
        } else {
            None
        }
    }

    pub fn reply(&mut self, action: ConsoleAction) {
        if let Some(val) = match action {
            // ConsoleAction::Char(_) => todo!(),
            // ConsoleAction::Up => todo!(),
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
            write(val);
        }
    }

    pub fn backspace(&mut self) {
        //        let _ = self.buffer.data.remove(self.buffer.cursor);
        self.redraw_line();
    }

    pub fn split_list(&mut self) {
        // this is unsafe beacuse the full split uses the full unicode libs
        // and the firmware blows out by 7Kb.
        unsafe {
            let buf = &self.buffer.clone();
            let start = buf.data.get_unchecked(0..buf.cursor - 1);
            let end = buf.data.get_unchecked(buf.cursor..buf.data.len());

            write(start);
            write(end);
            self.buffer.reset();
            self.buffer.push_str(start);
            //self.buffer.push('|');
            self.buffer.push_str(end);
        }
    }
    pub fn redraw_line(&mut self) {
        //Clear line
        write("\x1b[2K");
        // Move al the way left
        write("\x1b[G");
        write(PROMPT);
        write(self.buffer.data.as_str());
    }

    pub fn clear_screen(&mut self) {
        write("\x1b[2J\x1b[H"); // clear screen and home
    }

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
                b'\x0D' => {
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
                                            if let Some(_) = self.serial.tget() {
                                                return Some(ConsoleAction::Home);
                                            }
                                        }
                                        b'\x32' => {
                                            if let Some(_) = self.serial.tget() {
                                                return Some(ConsoleAction::Insert);
                                            }
                                        }
                                        b'\x33' => {
                                            if let Some(_) = self.serial.tget() {
                                                return Some(ConsoleAction::Delete);
                                            }
                                        }
                                        b'\x34' => {
                                            if let Some(_) = self.serial.tget() {
                                                return Some(ConsoleAction::End);
                                            }
                                        }
                                        b'\x35' => {
                                            if let Some(_) = self.serial.tget() {
                                                return Some(ConsoleAction::PgUp);
                                            }
                                        }
                                        b'\x36' => {
                                            if let Some(_) = self.serial.tget() {
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
                    let _ = self.buffer.data.push(c as char);
                    self.buffer.cursor += 1;
                    return Some(ConsoleAction::Char(c));
                }
            }
        }
        None
    }
}
