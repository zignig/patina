from .memx import GenRust
from .memx import BootLoaderX
from .variables import RustLib
from .gensvd import GenSVD
from .res_list import ResList

import os
import logging 
log = logging.getLogger(__name__)

class RustArtifacts:
    def __init__(self, soc):
        self.soc = soc

    def make_svd(self,folder):
        # gs =  GenSVD(self.soc)      
        # gs.generate_svd()
        rs = ResList(self.soc)
        rs.generate()

    def make_bootloader(self,folder):
        rustlib = RustLib(self.soc)
        bloader = BootLoaderX(self.soc)

        log.info(f"Generate Bootloader Files in {folder}")
        try:
            os.stat(folder)
        except:
            os.mkdir(folder)
        memx = open(folder + os.sep + "memory.x", "w")
        bloader.generate_memory_x(memx)
        libx = open(folder + os.sep + "generated.rs", "w")
        rustlib.gen_lib_rs(libx)

    def make_memmap(self,folder):
        memmap = GenRust(self.soc)

        log.info(f"Generate memory.x in {folder}")
        if folder is not None:
            try:
                os.stat(folder)
            except:
                os.mkdir(folder)
            memx = open(folder + os.sep + "memory.x", "w")
            memmap.generate_memory_x(memx)
        else:
            memmap.generate_memory_x()

    def make_firmware(self,folder):
        rustlib = RustLib(self.soc)

        log.info(f"Generate Firmware Files in {folder}")
        if folder is not None:
            try:
                os.stat(folder)
            except:
                os.mkdir(folder)
            libx = open(folder + os.sep + "generated.rs", "w")
            rustlib.gen_lib_rs(libx)
        else:
            rustlib.gen_lib_rs()
