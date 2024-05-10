#!/usr/bin/env python

# This generates a image from a binary for uploading to upload to the 
# flash chip that can be booted from 

# for the TinyFpgaBX , this will start at 0x50000
# and the layout is as follows.
# header = 256 bytes (1 page of flash)
#   (0-3) program length (4 byte little endian) of the program
#   (4 - 256) - don't care , the rest of the header is empty for now

# +256 - length
# the program in little endian words

import argparse
import struct
import os
from pathlib import Path

def build_header(prog_length):
    # 256 byte block
    # TODO , version , checksum , stuff
    header = bytearray(256)
    struct.pack_into("<I",header,0,prog_length)
    return header

def load(file_name):
    bootloader = Path(file_name).read_bytes()
    boot_image = struct.unpack("<" + "I" * (len(bootloader) // 4), bootloader)
    return bytearray(bootloader)

if __name__  == "__main__":
    parser = argparse.ArgumentParser(
        prog="Flash image builder",
        description="takes a binary and prepares it for flash upload",
        epilog="woohoo"
    )
    parser.add_argument('filename')

    args = parser.parse_args()
    print(args)
    boot_image = load(args.filename)
    header = build_header(len(boot_image))
    full = header + boot_image
    print(full)
    f = open('test.bit','wb')
    f.write(full)
    f.close()