from .memx import GenRust
from .memx import BootLoaderX
from .variables import RustLib

import os
import logging 
log = logging.getLogger(__name__)

class RustArtifacts:
    def __init__(self, soc, folder=None):
        self.soc = soc
        self.folder = folder

    def make_bootloader(self):
        folder = self.folder

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

    def make_firmware(self):
        folder = self.folder

        rustlib = RustLib(self.soc)
        bloader = GenRust(self.soc)

        log.info(f"Generate Firmware Files in {folder}")
        if folder is not None:
            try:
                os.stat(folder)
            except:
                os.mkdir(folder)
            memx = open(folder + os.sep + "memory.x", "w")
            libx = open(folder + os.sep + "generated.rs", "w")
            bloader.generate_memory_x(memx)
            rustlib.gen_lib_rs(libx)
        else:
            bloader.generate_memory_x()
            rustlib.gen_lib_rs()
