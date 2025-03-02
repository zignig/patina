#!/usr/bin/env python

from amaranth import Elaboratable, Module
from amaranth.lib.wiring import connect

from amaranth_boards.resources.interface import UARTResource
from amaranth.build import Attrs

from hapenny.cpu import Cpu
from hapenny.serial import BidiUart
from hapenny.mem import BasicMemory
from hapenny.gpio import MinimalOutputPort

from patina.generate import *
from patina.fabric_builder import FabricBuilder, ProgramMemory
from patina.warmboot import WarmBoot
from patina.watchdog import Watchdog
from patina.spi import SimpleSPI
from patina.amcsr import Amcsr_bus, testp, compl
from patina import cli
from patina import log_base
import logging

from pathlib import Path
import struct

log = logging.getLogger(__name__)

# spinner = Path("firmware/bin/spinner").read_bytes()
# spin_image = struct.unpack("<" + "H" * (len(spinner) // 2), spinner)


class Computer(Elaboratable):
    def __init__(self, serial="/dev/ttyUSB0", baud=115200, firmware=None):
        F = 16e6  # Hz

        # cli uses these to connect
        self.serial = serial
        self.baud = baud
        self.firmware = firmware

        #t = testp()
        #t2 = testp()
        t3 = compl()

        super().__init__()
        # auto build binary
        self.mainmem = mainmem = ProgramMemory(depth=512)  # 16bit cells
        mainmem.set_file("firmware/bin/spinner")

        self.gpio_out = gpio_out = MinimalOutputPort(1)
        
        # CSR

        self.csr = Amcsr_bus([t3])
        devices = [self.mainmem, self.csr, gpio_out]

        self.fabric = fabric = FabricBuilder(devices)

        self.cpu = Cpu(reset_vector=fabric.reset_vector, addr_width=fabric.addr_width)

    def elaborate(self, platform):
        m = Module()
        # This creates and binds all the devices
        # Add the CPU
        m.submodules.cpu = self.cpu
        # Add the fabric
        m.submodules.fabric = self.fabric
        # Connect the cpu and the fabric
        connect(m, self.cpu.bus, self.fabric.bus)
        return m


async def bench(ctx):
    max = 4096
    for i in range(max):
        if i % 128 == 0:
            log.info(f"Remaining {max} - {max - i}")
        await ctx.tick()


from amaranth.sim import Simulator

if __name__ == "__main__":
    pooter = Computer()
    pooter.fabric.show()
    pooter.mainmem.build()
    sim = Simulator(pooter)
    sim.add_clock(1e-6)
    sim.add_testbench(bench)
    with sim.write_vcd("pooter.vcd"):
        sim.run()
