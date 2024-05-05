#![no_std]
#![no_main]

use rustv::{
    flash::Flash,
    generated,
    init::reset,
};

#[no_mangle]
pub extern "C" fn main() -> ! {
    pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;
    let mut flash: TinyFlash = Flash::new();
    flash.wakeup();
        
    loop {
        flash.simple_read(0x50000, 1290);
        reset();
    }
}
