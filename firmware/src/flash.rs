//! Flash  driver
//! taken from
//! https://github.com/tpwrules/ice_panel/commit/147969bdeedb5d4990045fcd4976b2f95704ad4c
//!
//! this rust code operates patina/spi.py

//! Converted from boneless assembly

//!  Register Map

//!  0x0: (W) Transaction Start / (R) Status
//!    Write: writing starts a transaction. it is only legal to start a transaction
//!           when one is not already in progress.
//!          bit 15: 1 for write transaction, 0 for read transaction
//!            14-13: bus mode: 0 = previous, 1 = 1 bit, 2 = 2 bit, 3 = 4 bit
//!               12: 1 if chip select should be deasserted at txn end
//!             11-0: transaction length
//!     Read: bit 15: 1 if transaction in progress, 0 otherwise. the transaction
//!                   FIFO is empty/full and the bus is idle iff this bit is 0
//!            14:13: current bus mode

//!  0x1: (W) Queue Write / (R) Receive Read/FIFO status
//!  Write:      7-0: character to write on bus. only legal if in write mode.
//!   Read:   bit 15: bit 0 of read character, if RX FIFO is not empty in read mode
//!           bit 14: 1 if RX fifo is empty, 0 otherwise (in read mode)
//!                   1 if TX fifo is full, 0 otherwise (in write mode)
//!              6-0: remaining bits of char, if RX fifo is not empty in read mode


use core::ops::{BitAnd, BitOr};

use patina_pac::uart::{Bind, DefaultSerial};
use patina_pac::{init::wait, println};

#[repr(u8)]
enum Commands {
    Wakeup = 0xAB,
    Jedec = 0x9F,
    FastRead = 0x0B,
}

/// The interface to the flash device on the SOC
/// TODO COnvert all of this to u32
pub struct Flash<const ADDR: u32, const START: u32, const SIZE: u32> {
    byte_counter: u16,
    chunk_bytes: u16,
    bytes_left: u16,
    in_transaction: bool,
}

impl<const ADDR: u32, const START: u32, const SIZE: u32> Default for Flash<ADDR, START, SIZE> {
    fn default() -> Self {
        Self::new()
    }
}

/// Make  the entire flash object an iterator
// TODO: put it some guard rails around transactions
impl<const ADDR: u32, const START: u32, const SIZE: u32> Iterator for Flash<ADDR, START, SIZE> {
    type Item = u8;

    fn next(&mut self) -> Option<Self::Item> {
        // This iterator needs to be a bit fancy
        // as the SPI interface has a 12 bit (2048)
        // maximum byte count. Needs chunking.
        //
        // Goes a little like this.

        // Chunk counter empty.
        if (self.chunk_bytes == 0) & (self.bytes_left > 0) {
            // if the counter is larger than CHUNK_SIZE
            if self.bytes_left > Self::CHUNK_SIZE {
                //println!("@");
                // There is at least one more chunck
                self.bytes_left -= Self::CHUNK_SIZE;
                self.chunk_bytes = Self::CHUNK_SIZE;
                // Do not drop the CS as the transaction continues
                self.txn_read(Self::CHUNK_SIZE, false);
            } else {
                // Last chunk, drop the CS at the end
                self.txn_read(self.bytes_left, true);
                //println!("|");
                self.chunk_bytes = self.bytes_left;
                self.bytes_left = 0;
            }
        }

        //println!("{}",self.byte_counter);
        if self.byte_counter > 0 {
            self.byte_counter -= 1;
            self.chunk_bytes -= 1;
            //println!("b-{}\r\n",self.chunk_bytes);
            return Some(self.read_data());
        }
        None
    }
}

/// Transaction manager for the flash , Read Only for now.
impl<const ADDR: u32, const START: u32, const SIZE: u32> Flash<ADDR, START, SIZE> {
    // Registers
    const STATUS: *mut u16 = ADDR as *mut u16;
    const DATA: *mut u16 = (ADDR + 2) as *mut u16;

    // Address Limits (TODO)
    // const START: u32 = START;
    // const SIZE: u32 = SIZE;

    // Internal Constants
    const CHUNK_SIZE: u16 = 2048; // will be 2048 after testing.

    /// Make a new flash device
    pub fn new() -> Self {
        Self {
            byte_counter: 0,
            in_transaction: false,
            chunk_bytes: 0,
            bytes_left: 0,
        }
    }

    /// Get status bit from the spi device
    fn txn_running(&mut self) -> bool {
        let mut val = unsafe { Self::STATUS.read_volatile() };
        //println!(">{:X}<\r\n", val);
        val = val.bitand(0x8000);
        val == 0x8000
    }

    /// Wait until the transaction has finished
    // ? Timeout counter
    fn txn_wait(&mut self) {
        while self.txn_running() {
            // spin
        }
    }

    /// Start a write transaction
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

    /// Start a read transaction
    fn txn_read(&mut self, len: u16, assert: bool) {
        let mut val: u16 = 0;
        // if true drop the CS pin after the read
        if assert {
            val = val.bitor(1 << 12);
        }
        val += len;
        unsafe {
            Self::STATUS.write_volatile(val);
        }
        self.in_transaction = true;
    }

    /// Write a byte into the data fifo.
    fn write_data(&mut self, data: u8) {
        unsafe {
            Self::DATA.write_volatile(data as u16);
        }
    }

    /// Read a byte out of the fifo
    // Register has some layout for fifo status
    // Check the top of the file
    // TODO , check the timeout loop
    fn read_data(&mut self) -> u8 {
        let mut val = unsafe { Self::DATA.read_volatile() };
        val = val.rotate_left(1);
        // if the last bit is set, the fifo is empty
        // we  should wait
        while val.bitand(0x8000) == 0x8000 {
            // spin ? timeout
        }
        // Just get the data byte
        val = val.bitand(0x00FF);
        val as u8
    }

    /// Send wake up to the flash
    pub fn wakeup(&mut self) {
        self.txn_write(1, true);
        self.write_data(Commands::Wakeup as u8);
        self.txn_wait();
        // wait for the flash to wake up.
        wait(256);
    }

    /// Read the JEDEC code from the flash chip
    pub fn read_jedec(&mut self) -> [u8; 3] {
        let mut id: [u8; 3] = [0; 3];

        self.txn_write(1, false);
        self.write_data(Commands::Jedec as u8);
        self.txn_wait();
        self.txn_read(3, true);

        for item in &mut id {
            *item = self.read_data();
        }

        id
    }

    /// Write the address of the read write to the flash
    /// Must be inside a transaction
    fn write_address(&mut self, mut addr: u32) {
        // Shift the data to 24 bit + padding byte.
        addr <<= 8;
        //println!("addr :");
        for octet in addr.to_be_bytes() {
            //println!("|{:x}|", octet);
            self.write_data(octet);
        }
        //println!("\r\n");
    }

    /// Get an iterator for bytes
    pub fn read_iter(&mut self, addr: u32, len: u16) -> impl Iterator<Item = u8> + '_ {
        // Start a FastRead transaction
        self.txn_write(5, false);
        self.write_data(Commands::FastRead as u8);
        self.write_address(addr);
        self.txn_wait();
        // Set up the counters for the iterator
        // TODO move this to the iterator
        //self.txn_read(len, true);
        self.byte_counter = len;
        self.bytes_left = len;
        // Return self as an iterator for bytes
        self.into_iter()
    }

    
    /// Read a 32 bit numbers from an address
    pub fn read_words(&mut self, addr: u32,len: u16) -> impl Iterator<Item = u32> + '_ {
        self.read_iter(addr,len * 4).array_chunks::<4>().map(|data|u32::from_le_bytes(data))
    }

    /// Read a block out of flash and print
    pub fn read_block(&mut self, addr: u32, len: u16) {
        for val in self.read_iter(addr, len){ 
            println!("{}",val);
        }
        println!("\r\n");
    }
}
