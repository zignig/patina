//! Watch dog interface
//!


/// Watchdog structure implied
pub type Watchdog = WatchdogDev<{crate::generated::WATCHDOG_ADDR}>;

pub struct WatchdogDev<const ADDR: u32>;

impl<const ADDR: u32> WatchdogDev<ADDR> {
    const STATUS: *mut u16 = ADDR as *mut u16;
    const COUNTER: *mut u16 = (ADDR + 2) as *mut u16;

    /// Create a new watch dog
    pub fn new() -> Self {
        Self {}
    }

    /// Poke the watchdog to  prevent it from activating.
    pub fn poke(&mut self) {
        unsafe {
            Self::STATUS.write_volatile(0);
        }
    }

    /// Read the lower half of the counter
    pub fn read(&mut self) -> u16 {
        unsafe { Self::COUNTER.read_volatile() }
    }
}
