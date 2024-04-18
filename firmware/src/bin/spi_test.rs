#![no_std]
#![no_main]

use rustv::{
    flash::Flash,
    generated,
    init::reset,
    uart::{Bind, DefaultSerial},
};

#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut ds = DefaultSerial::new();
    pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;
    let mut flash: TinyFlash = Flash::new();

    loop {
        ds.putb('w' as u8);
        flash.wakeup();
        ds.putb('j' as u8);
        let jd = flash.read_jedec();
        for i in jd{
            ds.putb(i);
        }
        reset();
    }
}
