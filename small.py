#!/usr/bin/env python
import struct
from pathlib import Path

from amaranth import Elaboratable, Module, Signal
from amaranth.lib.wiring import connect

from amaranth_boards.resources.interface import UARTResource
from amaranth.build import Resource, Pins, Attrs

import amaranth.lib.cdc

from hapenny.cpu import Cpu
from hapenny.serial import BidiUart
from hapenny.mem import BasicMemory

from patina.generate import *
from patina.fabric_builder import FabricBuilder, BootMem
from patina import cli
from patina import log_base
import logging

log = logging.getLogger(__name__)


class Computer(Elaboratable):
    def __init__(self):
        F = 16e6  # Hz
        super().__init__()
        self.mainmem = mainmem = BasicMemory(depth=512 * 8)  # 16bit cells
        self.bootmem = bootmem = BootMem()

        self.bidi = BidiUart(baud_rate=115200, oversample=4, clock_freq=F)

        devices = [
            self.mainmem,
            bootmem,
            self.bidi,
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

        uartpins = platform.request("uart", 0)
        rx_post_sync = Signal()
        m.submodules.rxsync = amaranth.lib.cdc.FFSynchronizer(
            i=uartpins.rx.i,
            o=rx_post_sync,
            o_domain="sync",
            init=1,
            stages=2,
        )
        m.d.comb += [
            uartpins.tx.o.eq(self.bidi.tx),
            self.bidi.rx.eq(rx_post_sync),
        ]

        return m


from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform


if __name__ == "__main__":
    platform = TinyFPGABXPlatform()

    platform.add_resources(
        [
            UARTResource(
                0, rx="A8", tx="B8", attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
            ),
            Resource(
                "boot", 0, Pins("H2", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
            ),
            Resource("user", 0, Pins("J1", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        ]
    )

    pooter = Computer()

    cli.run(platform, pooter)
