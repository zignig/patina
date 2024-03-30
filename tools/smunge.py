# load and ascii store the bootloader as ascii 
# and monkey patch it. 
# only the serial port address and the stack pointer change 
# make a few different versions and see what changes

import os
import struct
from pathlib import Path


def smunge(file_name):
    data = Path(file_name).read_bytes()
    boot_image = struct.unpack("<" + "I" * (len(data) // 4), data)
    #print(enc.decode(encoding="ascii"))
    #print()
    return boot_image

def compare(first,second):
    if not (len(first) == len(second)):
        print('different lengths')
        return 
    for item in range(len(first)):
        #print(first[item],end=" ")
        #print(first[item],end="")
        if first[item] != second[item]:
            print(item,'|\t',bin(first[item]),'\t',bin(second[item]))

if __name__ == "__main__":
    print("binerizer")
    print("")
    files =  os.listdir(".")
    binaries = []
    for i in files:
        if i.endswith('bin'):
            print(i)
            binaries.append(i)

    encoded = []
    for i in binaries:
        encoded.append(smunge(i))
    
    for i in encoded:
        print(i)
    
    compare(encoded[0],encoded[1])
    