#![no_std]
#![no_main]

use rustv::{
    flash::Flash,
    generated,
    init::reset,
    uart::{Bind,DefaultSerial},
    println
};

#[no_mangle]
pub extern "C" fn main() -> ! {
    pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;
    let mut flash: TinyFlash = Flash::new();
    let mut ds = DefaultSerial::new();

    flash.wakeup();
        
    loop {
        for c in flash.read_iter(0x50000,1290){
            ds.putb(c);
        }
        println!("\r\ndone\r\n");
        reset();
    }
}
