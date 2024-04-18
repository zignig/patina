// Flash  driver
// taken from
// https://github.com/tpwrules/ice_panel/commit/147969bdeedb5d4990045fcd4976b2f95704ad4c

// Converted from boneless assembly

//  Register Map

//  0x0: (W) Transaction Start / (R) Status
//    Write: writing starts a transaction. it is only legal to start a transaction
//           when one is not already in progress.
//           bit 15: 1 for write transaction, 0 for read transaction
//            14-13: bus mode: 0 = previous, 1 = 1 bit, 2 = 2 bit, 3 = 4 bit
//               12: 1 if chip select should be deasserted at txn end
//             11-0: transaction length
//     Read: bit 15: 1 if transaction in progress, 0 otherwise. the transaction
//                   FIFO is empty/full and the bus is idle iff this bit is 0
//            14:13: current bus mode

//  0x1: (W) Queue Write / (R) Receive Read/FIFO status
//  Write:      7-0: character to write on bus. only legal if in write mode.
//   Read:   bit 15: bit 0 of read character, if RX FIFO is not empty in read mode
//           bit 14: 1 if RX fifo is empty, 0 otherwise (in read mode)
//                   1 if TX fifo is full, 0 otherwise (in write mode)
//              6-0: remaining bits of char, if RX fifo is not empty in read mode

use core::ops::{BitAnd, BitOr};

use crate::init::wait;

#[repr(u8)]
enum Commands {
    Wakeup = 0xAB,
    Jedec = 0x9F,
}
pub struct Flash<const ADDR: u32, const START: u32, const SIZE: u32>;

impl<const ADDR: u32, const START: u32, const SIZE: u32> Flash<ADDR, START, SIZE> {
    // Registers
    const STATUS: *mut u16 = ADDR as *mut u16;
    const DATA: *mut u16 = (ADDR + 2) as *mut u16;
    // Address Limits
    // const START: *mut u32 = START as *mut u32;
    // const SIZE: *mut u32 = SIZE as *mut u32;

    pub fn new() -> Self {
        Self {}
    }

    fn txn_running(&mut self) -> bool{
        let mut val = unsafe { Self::STATUS.read_volatile() };
        val = val.bitand(0x8000);
        val != 0
    }
    
    fn txn_wait(&mut self) { 
        while self.txn_running(){ 
            // spin
        }
    }

    fn txn_write(&mut self, len: u16, assert: bool) {
        // make it a write
        let mut val: u16 = 1 << 15;
        // deassert the cs pin after transaction
        if assert {
            val = val.bitor(1 << 12);
        }
        // set the length of the transaction
        val += len;
        unsafe {
            Self::STATUS.write_volatile(val);
        }
    }

    fn txn_read(&mut self, len: u16, assert: bool){
        let mut val: u16 = 0;
        if assert {
            val = val.bitor(1 << 12);
        }
        val += len;
        unsafe {
            Self::STATUS.write_volatile(val);
        }
    }

    fn write_data(&mut self, data: u8) {
        unsafe {
            Self::DATA.write_volatile(data as u16);
        }
    }

    fn read_data(&mut self) -> u8{
        let mut val = unsafe { Self::DATA.read_volatile() };
        val = val.rotate_left(1).bitand(0x00FF);
        val as u8
    }

    pub fn wakeup(&mut self) {
        self.txn_write(1, true);
        self.write_data(Commands::Wakeup as u8);
        self.txn_wait();
        // wait for the
        wait(1000);
    }

    pub fn read_jedec(&mut self) -> [u8;3]{
        let mut id: [u8;3] = [0;3];

        self.txn_write(1,false);
        self.write_data(Commands::Jedec as u8);
        self.txn_wait();
        self.txn_read(3,true);
        for pos in 0..3{
            id[pos] = self.read_data();
        }
        return id
    }

}
