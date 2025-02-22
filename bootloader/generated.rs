/*
 * Automatically generated by PATINA; edits will be discarded on rebuild.
 * (Most header files phrase this 'Do not edit.'; be warned accordingly.)
 *
 * Generated: 2025-02-22 20:23:28.644985.
 */

/// BIDIUART
pub const BIDIUART_ADDR: u32 = 0x8000 ; // 32768

/// WARMBOOT
pub const WARMBOOT_ADDR: u32 = 0xC000 ; // 49152

/// WATCHDOG
pub const WATCHDOG_ADDR: u32 = 0x10000 ; // 65536

/// SIMPLESPI
pub const SIMPLESPI_ADDR: u32 = 0x14000 ; // 81920
// extra settings for device
pub const SIMPLESPI_START_ADDR: u32 = 0xC350 ; // 50000 
pub const SIMPLESPI_FLASH_SIZE: u32 = 0x400 ; // 1024 

/// Reset Vector
pub const RESET_VECTOR: u32 = 0x4000; // 16384
/// Date stamp when this file was generated
pub const DATE_STAMP: &str = "2025-02-22 20:23:28.645121";
