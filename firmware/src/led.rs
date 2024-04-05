
pub type ActualLed = Led<{crate::generated::OUTPUTPORT_ADDR }>;
pub struct Led<const WARM: u32>;

impl<const LED: u32> Led<LED> {
    pub const ADDR: *mut u32 = LED as *mut u32;
    pub fn new() -> Self {
        Self {}
    }

    pub fn addr(&mut self) -> u32 { 
        return Self::ADDR as u32 ;
    }

    pub fn on(&mut self) {
        unsafe {
            Self::ADDR.write_volatile(1);
        }
    }

    pub fn off(&mut self) {
        unsafe {
            Self::ADDR.write_volatile(0);
        }
    }
}
