#![no_std]
#![no_main]

use patina_pac::{
    init::reset,
    println,
    uart::{Bind, DefaultSerial},
    watchdog::Watchdog,
};

use corncobs;
// use heapless::Vec;
use hubpack::{self, SerializedSize};

mod commands;
use commands::Command;

mod transport;
use transport::Transport;

// Transport testing type
pub type SerialTransport = Transport<Command, { corncobs::max_encoded_len(Command::MAX_SIZE) }>;

#[unsafe(no_mangle)]
pub extern "C" fn main() -> ! {
    //let mut ds = DefaultSerial::new();
    let mut ser_tr = SerialTransport::new();
    let mut out_buf: [u8; SerialTransport::COBS_SIZE] = [0; SerialTransport::COBS_SIZE];
    loop {
        let com = Command::Inserter(commands::Other::Two(false));
        // println!("{:?}",com);
        let size = ser_tr.encode(com, &mut out_buf).unwrap();

        let mut decoded_com: Command = Command::default();
        for c in out_buf[..size].iter() {
            // println!("{} - {:?}", i,  c);
            if let Some(item) = ser_tr.add(c) {
                decoded_com = item;
            }
        }
        // println!("{:?}",decoded_com);
        if decoded_com == com {
            println!("THE SAME");
        } else {
            println!("DIFFERENT");
        }
        println!("finish");
        reset();
    }
}

// let mut q = Vec::<Command, 8>::new();
// let mut tbuf: [u8; 20] = [0; 20];
// let mut rbuf: [u8; 20] = [0; 20];
// let mut obuf: [u8; 20] = [0; 20];
// let _ = q.push(Command::Big(12345, 56768));
// let _ = q.push(Command::Data(-99, 100));
// let _ = q.push(Command::Start);
// let _ = q.push(Command::Stop);
// let _ = q.push(Command::Fail);
// let _ = q.push(Command::Inserter(Other::Two(false)));
// //let _ = q.push_back(Command::Extra(Info{ item: 1, active: false , id: *b"blaf" }));
// println!("Decode check");
// println!("");
// wait(10);
// println!("max size {:?}", Command::MAX_SIZE);
// loop {

//     if !q.is_empty() {
//         if let Some(c) = q.pop() {
//             // Encode
//             println!("incoming -> {:?}", c);
//             let a = hubpack::serialize(&mut tbuf, &c).unwrap();
//             println!("-> hubpack : {:?}", &tbuf[..a]);
//             let b = corncobs::encode_buf(&tbuf[..a], &mut rbuf);
//             let sl = &mut rbuf[..b];
//             println!("-> corncob {:?}", sl);
//             // Decode
//             let n = corncobs::decode_buf(sl, &mut obuf).unwrap();
//             println!("<- corncob {:?}", obuf[..n]);
//             let out = hubpack::deserialize::<Command>(&obuf[..n]).unwrap();
//             println!("<- hubpack {:?}", out.0);
//             println!("-----");
//         }
//     } else {
//         reset();
//     }
// }
