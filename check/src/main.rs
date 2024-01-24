
use std::io::{stdout, Write};

static SOME_STRING: &[&str] = &[
    "this is a longer test to see if it changes!",
    "two",
    "three",
    "four",
    "five",
    "woot, NOPE its still broken",
    "seven",
];

fn main() {
    //let ds = DefaultSerial::new();
    loop {
        println!("size - {}\r\n", usize::MAX);
        println!("{} - {}\r\n", SOME_STRING[0], SOME_STRING[0].len());
        println!("{} - {}\r\n", SOME_STRING[1], SOME_STRING[1].len());
        println!("{} - {}\r\n", SOME_STRING[2], SOME_STRING[2].len());
        println!("{} - {}\r\n", SOME_STRING[3], SOME_STRING[3].len());
        println!("{} - {}\r\n", SOME_STRING[4], SOME_STRING[4].len());
        println!("{} - {}\r\n", SOME_STRING[5], SOME_STRING[5].len());
        println!("{} - {}\r\n", SOME_STRING[6], SOME_STRING[6].len());
        
        println!("\r\n");
        // var index testing
        println!("array length - {}",SOME_STRING.len());
        println!("\r\n");
        // if this is longer than 2 is give jibberish as the length
        for j in 0..5{
            println!("{}\r\n", SOME_STRING[j].len());
        }
        println!("\r\n");
        // set iter test
        for j in 0..SOME_STRING.len() {
            let l = SOME_STRING[j].len();
            println!("{} - {} - {}\r\n", j, l,SOME_STRING[j]);
        }
        break;
    }
}
