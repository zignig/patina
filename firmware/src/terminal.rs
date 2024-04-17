use crate::println;
use crate::uart::{Bind, DefaultSerial};

const BOX: &[&str] = &["┌─┬┐", "│ ││", "├─┼┤", "└─┴┘"];

pub fn show_boxen() { 
    for i in BOX{
        println!("{}",i);
    }
}
pub fn rectangle(w: usize, h: usize) {
    let top = BOX[0];
    per(top, 0);
    for _ in 0..w - 2 {
        per(top, 1);
    }
    per(top, 3);

    for _ in 0..h - 2 {
        println!("\r\n");
        let middle = BOX[1];
        per(middle, 0);
        for _ in 0..w - 2 {
            per(middle, 1);
        }
        per(middle, 3);
    }
    println!("\r\n");
    let bottom = BOX[3];
    per(bottom, 0);
    for _ in 0..w - 2 {
        per(bottom, 1);
    }
    per(bottom, 3);
}

//#[inline(never)]
fn per(s: &str, i: usize) {
    println!("{}", s.chars().nth(i).unwrap());
}
