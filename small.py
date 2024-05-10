#!/usr/bin/env python

import itertools
import argparse
import struct
from pathlib import Path
import sys

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.build import Resource, Pins, Attrs
from amaranth_boards.resources.interface import UARTResource
import amaranth.lib.cdc

from hapenny.cpu import Cpu
from hapenny.bus import SimpleFabric, partial_decode
from hapenny.serial import BidiUart

from hapenny.mem import BasicMemory, SpramMemory
from hapenny.gpio import OutputPort, InputPort

from patina.warmboot import WarmBoot

from patina.spi import SimpleSPI

from patina.generate import *

from patina.fabric_builder import FabricBuilder, BootMem

# Logging
import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.ERROR)

log = root_logger.getChild("computer")

# tiny-bootloader is written in a high-level language and needs to have a stack,
bootloader = Path("bootloader/small.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)

log.info("image_size {}", 2 ** (len(boot_image)).bit_length())


class Computer(Elaboratable):
    def __init__(self):
        F = 12e6  # Hz
        super().__init__()

        self.mainmem = mainmem = BasicMemory(depth=512 * 4)  # 16bit cells
        # self.othermem = othermem = BasicMemory(depth=512 * 3)
        # secondmem = SpramMemory()
        # thirdmem = SpramMemory()
        mem1 = SpramMemory()
        mem2 = SpramMemory()
        mem3 = SpramMemory()
        mem4 = SpramMemory()
        
        self.bootmem = bootmem = BootMem(boot_image)

        # these are attached to self so they can be altered in elaboration.

        self.bidi = BidiUart(baud_rate=115200, oversample=4, clock_freq=F)
        self.spi = SimpleSPI(fifo_depth=512)
        self.warm = WarmBoot()

        devices = [
            mem1,
            mem2,
            mem3,
            mem4,
            bootmem,
            self.bidi,
            self.spi,
            #self.warm,
        ]

        self.fabric = fabric = FabricBuilder(devices)

        self.cpu = Cpu(
            reset_vector=fabric.reset_vector, addr_width=fabric.addr_width
        )

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
        flash = True

        if flash:
            spi_pins = platform.request("spi_flash_1x")

            m.d.comb += [
                # peripheral to outside world
                spi_pins.clk.o.eq(self.spi.clk),
                spi_pins.cs.o.eq(~self.spi.cs),
                spi_pins.copi.o.eq(self.spi.copi),
                self.spi.cipo.eq(spi_pins.cipo.i),
            ]

        if uart:
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


from amaranth_boards.icebreaker import ICEBreakerPlatform
p = ICEBreakerPlatform()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Patina Running on tinybx",
        description="riscv32i mini soc",
        epilog="awesome!",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-b", "--build", action="store_true")
    parser.add_argument("-m", "--mapping", action="store_true")
    parser.add_argument("-g", "--generate", action="store_true")
    parser.add_argument("-l", "--loader", action="store_true")

    args = parser.parse_args()
    if args.verbose == 1:
        root_logger.setLevel(logging.INFO)
    elif args.verbose == 2:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.WARNING)

    log.info("Building Patina")
    log.debug("Debug mode on")

    pooter = Computer()
    # if args.verbose:
    #     pooter.memory_map = pooter.fabric.memory_map
    if args.loader:
        ra = RustArtifacts(pooter, folder="bootloader")
        ra.make_bootloader()
    if args.generate:
        ra = RustArtifacts(pooter, folder="firmware")
        ra.make_firmware()

    if args.build:
        p.build(pooter, do_program=True)