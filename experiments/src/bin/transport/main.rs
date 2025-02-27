#![no_std]
#![no_main]


use patina_pac::{
    init::{reset, wait},
    println,
    uart::{Bind, DefaultSerial},
};

use corncobs;
use heapless::Deque;
use hubpack;

mod commands;
use commands::{Command,Other,Info};

#[no_mangle]
pub extern "C" fn main() -> ! {
    //let mut ds = DefaultSerial::new();
    let mut q = Deque::<Command, 8>::new();
    let mut tbuf: [u8; 20] = [0; 20];
    let mut rbuf: [u8; 20] = [0; 20];
    let mut obuf: [u8; 20] = [0;20];
    let _ = q.push_back(Command::Big(12345, 56768, 90123));
    let _ = q.push_back(Command::Data(100, 100));
    let _ = q.push_back(Command::Start);
    let _ = q.push_back(Command::Stop);
    let _ = q.push_back(Command::Fail);
    let _ = q.push_back(Command::Inserter(Other::Two(false)));
    let _ = q.push_back(Command::Extra(Info{ item: 1, active: false , id: *b"blaf" }));
    println!("Decode check");
    println!("");
    wait(10);
    loop {
        if !q.is_empty() {
            if let Some(c) = q.pop_front() {
                // Encode
                println!("incoming -> {:?}", c);
                let a = hubpack::serialize(&mut tbuf, &c).unwrap();
                println!("-> hubpack : {:?}",&tbuf[..a]);
                let b = corncobs::encode_buf(&tbuf[..a], &mut rbuf);
                let sl = &mut rbuf[..b];
                println!("-> corncob {:?}", sl);
                // Decode
                let n = corncobs::decode_buf(sl,&mut obuf).unwrap();
                println!("<- corncob {:?}",obuf[..n]);
                let out = hubpack::deserialize::<Command>(&obuf[..n]).unwrap();
                println!("<- hubpack {:?}",out.0);
                println!("-----");
            }
        } else {
            reset();
        }
    }
}
