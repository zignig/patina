use crate::init;
use crate::println;
use crate::uart::{Bind, DefaultSerial};
use heapless::String;
use ufmt::derive::uDebug;

#[derive(uDebug)]
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
}

const BUF_SIZE: usize = 64;

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
                        println!("{}", (c as char));
                    }
                    None
                }
                // Ignore up and down , no history yet
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

                // Ignore as well
                ConsoleAction::PgUp => None,
                ConsoleAction::PgDown => None,

                // ConsoleAction::Escape => todo!(),
                // ConsoleAction::Tab => todo!(),
                // ConsoleAction::Cancel => todo!(),
                // ConsoleAction::Reset => todo!(),
                // ConsoleAction::Enter => todo!(),
                // ConsoleAction::BackSpace => todo!(),

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
            println!("{}", val);
        }
    }

    pub fn clear_screen(&mut self) {
        println!("\x1b[2J\x1b[H"); // clear screen and home
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
                    init::reset();
                    return Some(ConsoleAction::Reset);
                }
                b'\x09' => {
                    return Some(ConsoleAction::Tab);
                }
                b'\x0D' => {
                    // Enter
                    // let data = buffer.data.as_str();
                    // run_command(data);
                    // buffer.reset();
                    // println!("\r\n{}", PROMPT);
                    return Some(ConsoleAction::Enter);
                }
                b'\x7f' => {
                    //println!("backspace");
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
                                            //println!("up");
                                            return Some(ConsoleAction::Up);
                                        }
                                        b'\x42' => {
                                            //println!("down");
                                            return Some(ConsoleAction::Down);
                                        }
                                        b'\x43' => {
                                            //println!("right");
                                            return Some(ConsoleAction::Right);
                                        }
                                        b'\x44' => {
                                            //println!("left");
                                            return Some(ConsoleAction::Left);
                                        }
                                        b'\x31' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("home{}", c);
                                                return Some(ConsoleAction::Home);
                                            }
                                        }
                                        b'\x32' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("insert{}", c);
                                                return Some(ConsoleAction::Insert);
                                            }
                                        }
                                        b'\x33' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("delete{}", c);
                                                return Some(ConsoleAction::Delete);
                                            }
                                        }
                                        b'\x34' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("end{}", c);
                                                return Some(ConsoleAction::End);
                                            }
                                        }
                                        b'\x35' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("pg up{}", c);
                                                return Some(ConsoleAction::PgUp);
                                            }
                                        }
                                        b'\x36' => {
                                            if let Some(_) = self.serial.tget() {
                                                //println!("pg down{}", c);
                                                return Some(ConsoleAction::PgDown);
                                            }
                                        }

                                        _ => {
                                            println!("c, <{:x}>", c);
                                            return None;
                                        }
                                    }
                                }
                            }
                            _ => {
                                println!("unknown, <{:x}>", c);
                                return None;
                            }
                        }
                    } else {
                        //println!("escape only")
                        return Some(ConsoleAction::Escape);
                    }
                }
                _ => {
                    //self.serial.putb(c);
                    //println!(">{:x}<\r\n", c);
                    let _ = self.buffer.data.push(c as char);
                    self.buffer.cursor += 1;
                    return Some(ConsoleAction::Char(c));
                }
            }
        }
        None
    }
}
