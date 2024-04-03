
pub type ActualWarm = Warmboot<{crate::generated::WARMBOOT_ADDR }>;
pub struct Warmboot<const WARM: u32>;

impl<const WARM: u32> Warmboot<WARM> {
    pub const ADDR: *mut i16 = WARM as *mut i16;
    pub fn new() -> Self {
        Self {}
    }

    pub fn addr(&mut self) -> i16 { 
        return Self::ADDR as i16 ;
    }

    pub fn write(&mut self) {
        unsafe {
            Self::ADDR.write_volatile(1);
        }
    }
}
