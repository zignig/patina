#!/usr/bin/env python

import sys

sys.path.append("../")

import argparse
import struct
from pathlib import Path

from amaranth import *
from amaranth.lib.wiring import *

from hapenny.cpu import Cpu
from hapenny.serial import BidiUart

from hapenny.mem import BasicMemory
from hapenny.bus import SimpleFabric, partial_decode
from hapenny.gpio import OutputPort

from patina.spi import SimpleSPI

from generate import *
from patina.fabric_builder import FabricBuilder, BootMem

from amaranth.sim import Simulator, Tick

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
bootloader = Path("bus_test/spi.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)


class Computer(Elaboratable):
    def __init__(self):
        F = 16e6  # Hz
        super().__init__()

        self.mainmem = mainmem = BasicMemory(
            depth=512 * 2 , contents=boot_image
        )  # 16bit cells
        # self.mainmem = mainmem = BasicMemory(depth=512 * 4)  # 16bit cells

        # these are attached to self so they can be altered in elaboration.

        self.spi = SimpleSPI(fifo_depth=512)
        self.output = OutputPort(pins=9)

        devices = [
            mainmem,
            self.spi,
            self.output
        ]

        self.fabric = fabric = FabricBuilder(devices)

        self.cpu = Cpu(addr_width=fabric.addr_width)

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
        # m.submodules.spi = self.spi
        # m.submodules.iofabric = fabric = SimpleFabric(
        #     [
        #         partial_decode(m, self.mainmem.bus, 14),  # 0x____0000
        #         partial_decode(m, self.spi.bus, 14),  # 0x____1000
        #     ]
        # )
        connect(m, self.cpu.bus, self.fabric.bus)

        # spi_pins = platform.request("spi_flash_1x")
        # m.d.comb += [
        #     # peripheral to outside world
        #     spi_pins.clk.o.eq(self.spi.clk),
        #     spi_pins.cs.o.eq(self.spi.cs),
        #     spi_pins.copi.o.eq(self.spi.copi),
        #     self.spi.cipo.eq(spi_pins.cipo.i),
        # ]

        return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Patina Running on tinybx",
        description="riscv32i mini soc",
        epilog="awesome!",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-s", "--simulate", action="store_true")
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
        ra = RustArtifacts(pooter, folder="bus_test")
        ra.make_firmware()

    if args.simulate:
        os.chdir("bus_test")
        os.system("./go.sh")
        os.chdir("../")
        log.critical("SIMULATE")
        sim = Simulator(pooter)
        sim.add_clock(1e-6)

        def process():
            counter = 0
            while True:
                yield Tick()
                log.warning(counter)
                counter += 1
                if counter == 10000:
                    return

        sim.add_process(process)
        with sim.write_vcd(vcd_file="test.vcd"):
            sim.run()
