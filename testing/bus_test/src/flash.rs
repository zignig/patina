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
//use core::u32;
use crate::wait;

#[repr(u8)]
enum Commands {
    Wakeup = 0xAB,
    Jedec = 0x9F,
    FastRead = 0x0B,
}

pub struct Flash<const ADDR: u32, const START: u32, const SIZE: u32>;

impl<const ADDR: u32, const START: u32, const SIZE: u32> Flash<ADDR, START, SIZE> {
    // Registers
    const STATUS: *mut u16 = ADDR as _;
    const DATA: *mut u16 = (ADDR + 2) as _;
    // Address Limits
    // const START: *mut u32 = START as *mut u32;
    // const SIZE: *mut u32 = SIZE as *mut u32;

    pub fn new() -> Self {
        Self {}
    }

    // Get status bit from the spi device
    fn txn_running(&mut self) -> bool {
        let mut val = unsafe { Self::STATUS.read_volatile() };
        val = val.bitand(0x8000);
        val == 0x8000
    }

    // Wait until the transaction has finished
    fn txn_wait(&mut self) {
        while self.txn_running() {
            // spin
        }
    }

    // Start a write transaction
    pub fn txn_write(&mut self, len: u16, assert: bool) {
        // make it a write
        let mut val: u16 = 0;
        val = val.bitor(1 << 15);
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

    // Start a read transaction
    pub fn txn_read(&mut self, len: u16, assert: bool) {
        let mut val: u16 = 0;
        if assert {
            val = val.bitor(1 << 12);
        }
        //val += len;
        val = 0xABCD;
        unsafe {
            Self::STATUS.write_volatile(val);
        }
    }

    // Write a byte into the data fifo.
    pub fn write_data(&mut self, data: u8) {
        unsafe {
            Self::DATA.write_volatile(data as u16);
        }
    }

    // Read a byte out of the fifo
    // Register has some layout for fifo status
    // Check the top of  the file
    // TODO , check the timeout loop
    pub fn read_data(&mut self) -> u8 {
        let mut val = unsafe { Self::DATA.read_volatile() };
        val = val.rotate_left(1).bitand(0x00FF);
        val as u8
    }

    // Send wake up to the flash
    pub fn wakeup(&mut self) {
        self.txn_write(1, true);
        self.write_data(Commands::Wakeup as u8);
        self.txn_wait();
        // wait for the flash to wake up.
        wait(10000);
    }

    // Read the JEDEC code from the flash chip
    pub fn read_jedec(&mut self) -> [u8; 3] {
        let mut id: [u8; 3] = [0; 3];
        self.txn_write(1, false);
        self.write_data(Commands::Jedec as u8);
        self.txn_wait();
        self.txn_read(3, true);

        for pos in 0..id.len() {
            id[pos] = self.read_data();
        }

        return id;
    }

    // Write the address of the read write to the flash
    // Must be inside a transaction
    pub fn write_address(&mut self, addr: u32) {
        for octet in addr.to_be_bytes() {
            self.write_data(octet);
        }
    }

    pub fn read_block(&mut self, addr: u32, len: u16) {
        self.txn_write(5, false);
        self.write_data(Commands::FastRead as u8);
        self.write_address(addr << 12);
        self.txn_wait();
        self.txn_read(len, true);
        for _i in 0..len {
            let _data = self.read_data();
        }
    }
}
