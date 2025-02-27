use serde_derive::{Deserialize, Serialize};
use ufmt::derive::uDebug;

#[derive(uDebug, Clone, Copy, Deserialize, Serialize)]
pub enum Other { 
    One,
    Two(bool),
    Three(u8)
}
#[derive(uDebug, Clone, Copy, Deserialize, Serialize)]
pub struct Info { 
    pub item : u8,
    pub active: bool,
    pub id: [u8;4]
}

#[derive(uDebug, Clone, Copy, Deserialize, Serialize)]
pub enum Command { 
    Start,
    Stop,
    Data(u8,u8),
    Error,
    Fail,
    Big(u32,u32,u32),
    Inserter(Other),
    Extra(Info)
}

impl Default for Command {
    fn default() -> Self {
        Command::Fail
    }
}