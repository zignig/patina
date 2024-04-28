#![no_std]
#![no_main]


use core::arch::global_asm;
use bus_test::flash::Flash;
use patina_pac::led;
use bus_test::generated;

pub type TinyFlash = Flash<{ generated::SIMPLESPI_ADDR }, 0x50000, 0xFBFFF>;
pub type TheLed = Led<{gnereated::}
#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut my_flash = TinyFlash::new();
    my_flash.txn_read(1,true);
    my_flash.read_data();

    let mut my_led = 
    //my_flash.write_data(0xAA);
    //let _ = my_flash.read_jedec();
    //my_flash.read_block(0,128);
    loop {

    }
}

// -- no interupts yet.
#[no_mangle]
#[allow(non_snake_case)]
fn DefaultInterruptHandler() {}

global_asm! {
    "
    .pushsection .start,\"ax\",%progbits
    .globl __start
    __start:
        j main
    .popsection
    "
}

#[panic_handler]
unsafe fn my_panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

