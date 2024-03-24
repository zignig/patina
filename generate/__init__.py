from .memx import GenRust
from .memx import BootLoaderX
from .variables import RustLib

import os 

class RustArtifacts:
    def __init__(self,soc,folder=None):
        self.soc =  soc 
        self.folder = folder 

        bloader = BootLoaderX(soc)
        #bloader.generate_memory_x()

        firmware = GenRust(soc)
        #firmware.generate_memory_x()

        rustlib = RustLib(soc)
        #rustlib.gen_lib_rs()

        if folder is not None:
            print(folder)
            try:
                os.stat(folder)
            except:
                os.mkdir(folder)
            memx = open(folder+os.sep+"memory.x",'w')
            bloader.generate_memory_x(memx)
            libx = open(folder+os.sep+"generated.rs",'w')
            rustlib.gen_lib_rs(libx)
        else:
            bloader.generate_memory_x()
            rustlib.gen_lib_rs()
        
    def make_bootloader(self):
        folder = "tinyboot"
        
        rustlib = RustLib(self.soc)
        bloader = BootLoaderX(self.soc)

        print("Generate Files")
        try:
            os.stat(folder)
        except:
            os.mkdir(folder)
        memx = open(folder+os.sep+"memory.x",'w')
        bloader.generate_memory_x(memx)
        libx = open(folder+os.sep+"generated.rs",'w')
        rustlib.gen_lib_rs(libx)
        



