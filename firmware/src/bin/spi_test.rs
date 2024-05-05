#![no_std]
#![no_main]

#![feature(iter_array_chunks)]

use rustv::{
    flash::Flash,
    generated,
    init::reset,
    println,
    uart::{Bind, DefaultSerial},
};

pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;

#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut flash: TinyFlash = Flash::new();
    let mut ds = DefaultSerial::new();

    flash.wakeup();

    // const SIZE:u16 = 1290; 
    const SIZE:u16 = 65000; 
    loop {
        for data in flash.read_iter(0x50000,SIZE){ 
            //println!("{:X}",data);
            ds.putb(data);
        }
        //get_words(&mut flash,10);
        println!("\r\ndone\r\n");
        reset();
    }
}

//#[inline(never)]
// fn get_words(flash: &mut TinyFlash, mut words: u16) {
//     let count = words << 2;
//     let looper = flash.read_iter(0x50000, count);
//     let mut l2 = looper.array_chunks::<4>();
//     while words > 0 { 
//         let val = u32::from_le_bytes(l2.next().unwrap());
//         words -= 1;
//     }

//     // while words > 0 {
//     //     let mut word = u32::from(looper.next().unwrap());
//     //     word |= u32::from(looper.next().unwrap()) << 8;
//     //     word |= u32::from(looper.next().unwrap()) << 16;
//     //     word |= u32::from(looper.next().unwrap()) << 24;
//     //     println!("{:X}\r\n", word);
//     //     words -= 1;
//     // }
// }
