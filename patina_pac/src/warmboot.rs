
pub struct Warmboot<const WARM: u32>;

impl<const WARM: u32> Warmboot<WARM> {
    pub const ADDR: *mut u32 = WARM as *mut u32;
    pub fn new() -> Self {
        Self {}
    }

    pub fn addr(&mut self) -> u32 { 
        return Self::ADDR as u32 ;
    }

    pub fn write(&mut self) {
        unsafe {
            Self::ADDR.write_volatile(1);
        }
    }
}
