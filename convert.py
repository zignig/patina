# load a bin file and make a python array of 32bit words 

import struct 

file_name = 'test.bin'

f = open(file_name,'rb')
data = f.read()
f.close()

import io

def print_to_string(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


array = []
for i in struct.iter_unpack(">H",data):
    array.append(hex(i[0]))

r = print_to_string(array)
print(r)