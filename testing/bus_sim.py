import argparse

from pathlib import Path
import struct


from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth.back import verilog
from amaranth.lib.wiring import *
from amaranth.lib.enum import *

from hapenny.cpu import Cpu
from hapenny.bus import BusPort, partial_decode, SimpleFabric
from hapenny import *
from hapenny.mem import BasicMemory

from hapenny.gpio import OutputPort
from patina.spi import SimpleSPI
from patina.fabric_builder import FabricBuilder

import logging
from rich.logging import RichHandler

from spi import SimpleSPI

import logging

log = logging.getLogger(__name__)


RAM_WORDS = 256
RAM_ADDR_BITS = (RAM_WORDS - 1).bit_length()
BUS_ADDR_BITS = RAM_ADDR_BITS + 1

bootloader = Path("tinybx8k.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)

if __name__ == "__main__":
    m = Module()
    mem = BasicMemory(depth=512)
    #mem2 = BasicMemory(depth=32, name="second_mem")
    io = OutputPort(pins=4)
    bootmem = BootMem(boot_image,image_size=512)
    
    # fabric = SMCFabric([mem, mem2])#, io])
    flash = SimpleSPI()
    cpu = Cpu(addr_width=14)
    # cpu.add_device([mem3, mem2, mem, io, flash])
    # cpu.build(m)
    m.submodules.cpu = cpu
    m.submodules.flash = flash
    m.submodules.mem = mem
    m.submodules.bootmem = bootmem
    m.submodules.io = io

    m.submodules.iofabric = iofabric = SimpleFabric(
        [
            partial_decode(m, bootmem.bus, 11),  # 0x____1000
            partial_decode(m, mem.bus, 11),  # 0x____0000
            partial_decode(m,flash.bus,11)  # 0x____2000
        ]
    )
    connect(m, cpu.bus, iofabric.bus)

    # original fabric
    phase = Signal(State)

    sim = Simulator(m)
    sim.add_clock(1e-6)

    ports = [phase]

    # for i in cpu.memory_map.all_resources():
    #     print(i.path, i.start << 1, i.end << 1)

    # print()

    # for i in cpu.memory_map.window_patterns():
    #     print(i)

    # size = 2 ** (cpu.memory_map.addr_width - 1)
    # size = 1024
    # print(size)
    size = 1024
    def process():
        started = True
        #
        for i in range(size):
            yield
            if (i % 64) == 0 :
                print(i,size)
        # yield phase.eq(State.WRITE)
        # for i in range(size):
        #     yield from write_mem(i*2, i)
        #     print(i, hex(i))
        # yield phase.eq(State.READ)
        # for i in range(size):
        #     val = yield from read_mem(i*2)
        #     print(i, hex(val))

    sim.add_sync_process(process)

    with sim.write_vcd(vcd_file="test.vcd", gtkw_file="test.gtkw", traces=ports):
        sim.run()
