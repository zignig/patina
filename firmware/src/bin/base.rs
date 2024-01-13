#![no_std]
#![no_main]

use rustv::init::reset;
use rustv::println;
use rustv::uart::{Bind, DefaultSerial};


static SOME_STRING: &[&str] = &["one", "two", "three"];

#[no_mangle]
pub extern "C" fn main() -> ! {
    //Create a serial port
    let mut ds = DefaultSerial::new();
    println!("Base testing\r\n");

    loop {
        if let Some(c) = ds.get() {
            match c {
                32 => {
                    for char in 32..126 {
                        ds.putb(char);
                    }
                }
                b'\x03' => {
                    list();
                    let test = "this is a test";
                    println!("{}-{}", test, test.len());
                }
                b'\x04' => {
                    reset();
                }
                _ => {
                    //echo everything else
                    ds.putb(c);
                }
            }
        }
    }
}

fn list() {
    println!("\r\n");
    let first = SOME_STRING[0];
    println!("{}-{}\r\n", first, first.len());
    // for index in 0..SOME_STRING.len() {
    //     println!("{}-{}\r\n",index,SOME_STRING[index].len());
    // }
    for name in SOME_STRING.iter() {
        println!("{}\r\n",name.len());
    }
}

