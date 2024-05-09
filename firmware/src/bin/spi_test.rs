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

    //const SIZE: u16 = 1290;
    const START:u32 = 0x50000;
    const SIZE:u16 = 65000;

    loop {
        for data in flash.read_iter(START, SIZE) {
            //println!("{:X}",data);
            ds.putb(data);
        }
        println!("\r\n");
        // for words in flash.read_iter(0x50000,64).array_chunks::<4>(){
        //     //println!("{:?}\r\n",words);
        //     let num: u32 = u32::from_le_bytes(words);
        //     println!("{:?}\r\n",num);
        // }
        println!("\r\ndone\r\n");
        reset();
    }
}
