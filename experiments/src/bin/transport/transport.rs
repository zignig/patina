//! Take Enum and Structs and transport them across a serial port for now
//! Uses cobs and hubpack to serialize and frame the data for transport
//!
use core::char::MAX;

use corncobs;
use heapless::Vec;
use hubpack;
use serde;

pub struct Transport<T, const COBS_SIZE: usize> {
    incoming: Vec<T, 2>,
    incoming_bytes: Vec<u8, COBS_SIZE>,
    //outgoing: [u8; COBS_SIZE],
    //in_bus: [u8; COBS_SIZE],
}

impl<T, const COBS_SIZE: usize> Transport<T, COBS_SIZE>
where
    T: hubpack::SerializedSize,
    T: serde::de::DeserializeOwned,
    T: serde::ser::Serialize,
    //Self: IO,
{
    pub const COBS_SIZE: usize = COBS_SIZE;

    pub fn new() -> Self {
        Self {
            incoming: Vec::new(),
            incoming_bytes: Vec::new(),
            //outgoing: [0; COBS_SIZE],
            //in_bus: [0; COBS_SIZE],
        }
    }

    pub fn add(&mut self, c: &u8) -> Option<T> {
        // incoming char where there is a zero
        // it's the end of the frame , process
        // if *c == 0 && self.incoming_bytes.len() == 0 {
        //     // nothing in buffer ( errant zero )
        //     return None;
        // }
        match self.incoming_bytes.push(*c) {
            Ok(_) => {
                if *c == 0 {
                    // end of the frame
                    match self.decode() {
                        Ok(val) => {
                            // rest the vector
                            self.incoming_bytes.clear();
                            return Some(val);
                        }
                        Err(_) => todo!(),
                    }
                }
            }
            Err(_) => todo!(),
        }
        None
    }

    fn decode(&mut self) -> Result<T, ()> {
        let mut data = self.incoming_bytes.as_mut_slice();
        match corncobs::decode_in_place(&mut data) {
            Ok(size) => match hubpack::deserialize::<T>(&data[..size]) {
                Ok(val) => {
                    return Ok(val.0);
                }

                Err(_) => return Err(()),
            },
            Err(_) => Err(()),
        }
    }

    pub fn encode(&mut self, val: T, buf: &mut [u8]) -> Result<usize, ()> {
        // let mut buf: [u8; MAX_SIZE] = [0; MAX_SIZE];
        // waste's two bytes , but does not need genearic parameter
        let mut output: [u8; COBS_SIZE] = [0; COBS_SIZE];
        match hubpack::serialize(&mut output, &val) {
            Ok(hp_size) => {
                let cc_size = corncobs::encode_buf(&output[..hp_size], buf);
                return Ok(cc_size);
            }
            Err(_) => todo!(),
        }
    }
}

// pub trait IO {
//     fn inchar(&mut self) -> Option<u8>;
//     fn outchar(&mut self, c: u8);
// }
