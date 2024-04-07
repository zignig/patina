// Input pin handler
//

use core::ops::BitAnd;

// Get the pin address
// Make the struct
pub struct Input<const INPUT: u32>;
// Refence the Fixed address
pub type ActualInput = Input<{ crate::generated::INPUTPORT_ADDR }>;

impl<const INPUT: u32> Input<INPUT> {
    pub const ADDR: *mut u16 = INPUT as *mut u16;
    pub fn new() -> Self {
        Self {}
    }

    pub fn read(&mut self) -> u16 {
        unsafe { Self::ADDR.read_volatile() }
    }

    pub fn read_bit(&mut self,bit: u16) -> bool{         
        let mask: u16 = 0 << bit;
        let val: u16 = unsafe { Self::ADDR.read_volatile()};
        val.bitand(mask) != 0
    }
}
