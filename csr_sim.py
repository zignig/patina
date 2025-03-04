#!/usr/bin/env python

from amaranth import * 
from amaranth import Elaboratable, Module
from amaranth.lib.wiring import connect

from amaranth_boards.resources.interface import UARTResource
from amaranth.build import Attrs

from hapenny.cpu import Cpu

from patina.generate import *
from patina.fabric_builder import FabricBuilder, ProgramMemory
from patina.amcsr import Amcsr_bus
from patina import cli
from patina import log_base

from patina.peripheral.timer import Timer
from patina.peripheral.regtest import RegTest
import logging

log = logging.getLogger(__name__)


class Computer(Elaboratable):
    def __init__(self, serial="/dev/ttyUSB0", baud=115200, firmware=None):
        F = 16e6  # Hz

        # cli uses these to connect
        self.serial = serial
        self.baud = baud
        self.firmware = firmware

        super().__init__()
        # auto build binary
        self.mainmem = mainmem = ProgramMemory(depth=512)  # 16bit cells
        mainmem.set_file("experiments/bin/spinner")

        # CSR
        self.timer = timer = Timer()
        self.regtest = regtest = RegTest()
        self.csr = Amcsr_bus([regtest,timer])

        devices = [self.mainmem, self.csr]

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

        cycles = Signal(32)
        m.d.sync += cycles.eq(cycles+1)
        return m


async def bench(ctx):
    max = 2048
    for i in range(max):
        if i % 128 == 0:
            log.info(f"Remaining {max} - {max - i}")
        await ctx.tick()


from amaranth.sim import Simulator

if __name__ == "__main__":
    pooter = Computer()
    # build an artifact generator
    ra = RustArtifacts(pooter)
    # build the basic reg mapping for rust
    ra.make_firmware('experiments/src/bin/spinner')

    # show the memory mapping
    pooter.fabric.show()
    # build a fresh copy of the firmware
    pooter.mainmem.build()
    # show the register heirachy.
    cli.do_svd(pooter)

    sim = Simulator(pooter)
    sim.add_clock(1e-6)
    sim.add_testbench(bench)
    with sim.write_vcd("pooter.vcd"):
        sim.run()
