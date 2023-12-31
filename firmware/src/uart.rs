// Simple uart functions

// The uart address is generted by the build script
use core::convert::Infallible;
use ufmt::uWrite;


// Build magic env in .cargo/cargo.toml defines this address
pub type DefaultSerial = Serial<{ crate::generated::UART_ADDR }>;

pub struct Serial<const UART: i16>;

pub trait Bind {
    const RX: *mut i16;
    const TX: *mut u16;
    fn new() -> Self;
    fn txbusy(&mut self) -> bool;
    fn flush(&mut self);
    fn putb(&mut self, b: u8);
    fn getc(&mut self) -> u8;
    fn get(&mut self) -> Option<u8>;
}

impl<const UART: i16> Bind for Serial<UART> {
    const RX: *mut i16 = UART as *mut i16;
    const TX: *mut u16 = (UART + 2) as *mut u16;

    fn new() -> Self {
        Self {}
    }

    fn txbusy(&mut self) -> bool {
        unsafe { Self::TX.read_volatile() != 0 }
    }

    fn flush(&mut self) {
        while self.txbusy() {
            // spin
        }
    }

    fn putb(&mut self, b: u8) {
        self.flush();
        unsafe {
            Self::TX.write_volatile(u16::from(b));
        }
    }

    // blocking
    fn getc(&mut self) -> u8 {
        loop {
            let status = unsafe { Self::RX.read_volatile() };
            if status >= 0 {
                return status as u8;
            }
        }
    }

    fn get(&mut self) -> Option<u8> {
        let status = unsafe { Self::RX.read_volatile() };
        if status >= 0 {
            return Some(status as u8);
        }
        None
    }
}

// Some macros on the default serial
// give me the basics
// please ...
// write! and println! for the DefaultSerial
impl uWrite for DefaultSerial{
    type Error = Infallible;

    fn write_str(&mut self, s: &str) -> Result<(), Self::Error> {
        for c in s.as_bytes() { 
            self.putb(*c);
        }
        Ok(())
    }
}

// pub fn writer(s: &str){
//     let mut ds = DefaultSerial::new();
//     for c in s.as_bytes() { 
//         ds.putb(*c);
//     }
// }


#[macro_export]
macro_rules! println
{
	($($args:tt)+) => ({
			let _ = ::ufmt::uwrite!(DefaultSerial::new(), $($args)+);
	});
}

// #[macro_export]
// macro_rules! println
// {
// 	() => ({
// 		   print!("\r\n")
// 		   });
//     ($fmt:expr) => ({
// 			print!(concat!(fmt, "\r\n"))
// 			});
// 	($fmt:expr, $($args:tt)+) => ({
// 			print!(concat!($fmt, "\r\n"), $($args)+)
// 			});
// }
