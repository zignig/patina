//! Simple uart functions

// The uart address is generted by the build script
use core::option::*;
use core::convert::Infallible;

use ufmt::uWrite;

/// Bind a alias that points to the UART address
pub type DefaultSerial = Serial<{crate::generated::BIDIUART_ADDR }>;

/// Generic serial port struct
pub struct Serial<const UART: u32>;

/// Define a trait for all the basic serial port actions
pub trait Bind {
    /// Address of the recieve register
    const RX: *mut i16;
    /// Address of the transmit register
    const TX: *mut u16;
    /// Create a new serial port struct
    fn new() -> Self;
    /// Check if the serial port is busy
    fn txbusy(&mut self) -> bool;
    /// Wait for the TX to be empty
    fn flush(&mut self);
    /// Put a character into the UART
    fn putb(&mut self, b: u8);
    /// Get a char off the UART , blocking
    fn getc(&mut self) -> u8;
    /// Get an Option for a char of the UART
    fn get(&mut self) -> Option<u8>;
    /// Get a char with a timeout
    fn tget(&mut self) -> Option<u8>;
}

impl<const UART: u32> Bind for Serial<UART> {
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

    // #[inline(never)]
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
    
    // #[inline(never)]
    fn get(&mut self) -> Option<u8> {
        let status = unsafe { Self::RX.read_volatile() };
        if status >= 0 {
            return Some(status as u8);
        }
        None
    }

    // blocking get with timeout
    fn tget(& mut self) -> Option<u8> { 
        let mut counter: u32 = 0 ;
        loop {
            let status = unsafe { Self::RX.read_volatile() };
            if status >= 0 {
                return Some(status as u8);
            }
            counter += 1;
            if counter > 500{ 
                return None
            }
        }
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

/// Formatted printing
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
