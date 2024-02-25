use crate::println;
use crate::uart::{Bind, DefaultSerial};
use heapless::String;
use ufmt::derive::uDebug;


struct Buffer {
    data: String<32>,
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
}


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

pub struct Console<const ADDR: i16> {
    pub buffer: Buffer,
    pub serial: crate::uart::Serial<ADDR>,
}

impl<const ADDR: i16> Console<ADDR> {
    pub fn new() -> Self {
        Self {
            buffer: Buffer::new(),
            serial: crate::uart::Serial::<ADDR>::new(),
        }
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
                    //init::reset();
                    return Some(ConsoleAction::Reset);
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
                    self.serial.putb(c);
                    //println!(">{:x}<\r\n", c);
                    let _ = self.buffer.data.push(c as char);
                    return Some(ConsoleAction::Char(c));
                }
            }
        }
        None
    }
}
