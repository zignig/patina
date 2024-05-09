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

def build_header(prog_length):
    # 256 byte block
    # TODO , version , checksum , stuff
    header = bytes(256)
    struct.pack
    
if __name__  == "__main__":
    print('flash builder for patina')