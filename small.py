#!/usr/bin/env python

from amaranth import Elaboratable, Module, Signal
from amaranth.lib.wiring import connect

from amaranth_boards.resources.interface import UARTResource
from amaranth.build import Resource, Pins, Attrs

import amaranth.lib.cdc

from hapenny.cpu import Cpu
from hapenny.serial import BidiUart
from hapenny.mem import BasicMemory, SpramMemory

from patina.generate import *
from patina.fabric_builder import FabricBuilder, BootMem
from patina.warmboot import WarmBoot
from patina.watchdog import Watchdog
from patina.spi import SimpleSPI
from patina import cli
from patina import log_base
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
        self.mainmem = mainmem = BasicMemory(depth=512 * 5)  # 16bit cells
        self.bootmem = bootmem = BootMem()  # one bram , auto build
        self.warmboot = warmboot = WarmBoot()
        self.watchdog = watchdog = Watchdog()
        self.spi = spi = SimpleSPI()
        self.bidi = BidiUart(baud_rate=115200, oversample=4, clock_freq=F)

        devices = [
            self.mainmem,
            bootmem,
            self.bidi,
            self.warmboot,
            #self.watchdog,
            # self.spi,
        ]

        self.fabric = fabric = FabricBuilder(devices)

        self.cpu = Cpu(reset_vector=fabric.reset_vector, addr_width=fabric.addr_width)

    def elaborate(self, platform):
        m = Module()

        # This creates and binds all the devices
        # Add the CPU
        m.submodules.cpu = self.cpu
        # Add the fabric
        m.submodules.fabric = self.fabric
        # Bind the fabric (weird semantics in elaborate)
        self.fabric.bind(m)
        # Connect the cpu and the fabric
        connect(m, self.cpu.bus, self.fabric.bus)

        uart = True
        if uart:
            uartpins = platform.request("uart", 0)
            self.bidi.bind(m, uartpins)

        return m


from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform as ThePlatform

# from amaranth_boards.nandland_go import NandlandGoPlatform as ThePlatform
# from amaranth_boards.icestick import ICEStickPlatform as ThePlatform
# from amaranth_boards.icesugar import ICESugarPlatform as ThePlatform


if __name__ == "__main__":
    platform = ThePlatform()
 
    platform.add_resources(
        [
            UARTResource(
                0, rx="A8", tx="B8", attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
            ),
        ]
    )

    pooter = Computer(serial="/dev/ttyUSB0", baud=115200, firmware=["firmware", "base"])

    cli.run(platform, pooter)
