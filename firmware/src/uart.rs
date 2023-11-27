// Simple uart functions

// The uart address is generted by the build script
use core::fmt::Write;

// Default serial from build system
// magic include.
mod generated {
    include!(concat!(env!("OUT_DIR"), "/peripherals.rs"));
}

// Build magic env in .cargo/cargo.toml defines this address
pub type DefaultSerial = Serial<{ generated::UART_ADDR }>;

pub struct Serial<const UART: i16>;

pub trait Bind {
    const RX: *mut i16;
    const TX: *mut u16;
    fn new() -> Self;
    fn txbusy() -> bool;
    fn flush();
    fn putb(b: u8);
    fn getc() -> u8;
    fn get() -> Option<u8>;
}

impl<const UART: i16> Bind for Serial<UART> {
    const RX: *mut i16 = UART as *mut i16;
    const TX: *mut u16 = (UART + 2) as *mut u16;

    fn new() -> Self {
        Self {}
    }

    fn txbusy() -> bool {
        unsafe { Self::TX.read_volatile() != 0 }
    }

    fn flush() {
        while Self::txbusy() {
            // spin
        }
    }

    fn putb(b: u8) {
        Self::flush();
        unsafe {
            Self::TX.write_volatile(u16::from(b));
        }
    }

    // blocking
    fn getc() -> u8 {
        loop {
            let status = unsafe { Self::RX.read_volatile() };
            if status >= 0 {
                return status as u8;
            }
        }
    }

    fn get() -> Option<u8> {
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
// write! and println for the DefaultSerial

impl Write for DefaultSerial {
    fn write_str(&mut self, s: &str) -> Result {
        for c in s.as_bytes() {
            self.putb(c);
        }
        Ok(())
    }
}


