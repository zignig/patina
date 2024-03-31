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

from warmboot import WarmBoot

from spi import SimpleSPI

from generate import *

from fabric_builder import FabricBuilder, BootMem

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
bootloader = Path("boot8k.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)

log.info("image_size {}", 2 ** (len(boot_image)).bit_length())


class Computer(Elaboratable):
    def __init__(self):
        F = 16e6  # Hz
        super().__init__()

        self.mainmem = mainmem = BasicMemory(depth=512 * 8)  # 16bit cells
        #self.othermem = othermem = BasicMemory(depth=512 * 3)
        #secondmem = SpramMemory()
        #thirdmem = SpramMemory()
        self.bootmem = bootmem = BootMem(boot_image)

        # these are attached to self so they can be altered in elaboration.

        self.bidi = BidiUart(baud_rate=115200, oversample=4, clock_freq=F)
        self.led = OutputPort(1, read_back=True)
        self.input = InputPort(1)
        self.spi = SimpleSPI(fifo_depth=512)
        self.warm = WarmBoot()

        # devices = [bootmem,self.led]
        # devices = [
        #     secondmem,
        #     [thirdmem, mainmem, othermem],
        #     [bootmem, [self.bidi, self.spi], [self.led, self.input]],
        # ]
        # devices = [secondmem,mainmem,bootmem,self.bidi]
        # devices = [mainmem, bootmem, self.bidi, self.spi]

        devices = [mainmem, bootmem, self.bidi]#,self.warm]
        
        self.fabric = FabricBuilder(devices)

        self.cpu = Cpu(reset_vector=4096, addr_width=14)  # 4096 in half words

    def elaborate(self, platform):
        m = Module()

        # This creates and binds all the devices
        old = True
        if old:
            # cliffs default bus layout
            log.warning("Build  the bus")
            log.warning("")
            # old style bus
            m.submodules.cpu = self.cpu
            m.submodules.mainmem = mainmem = self.mainmem
            m.submodules.mem = bootmem = self.bootmem
            m.submodules.uart = uart = self.bidi
            #m.submodules.warm = warm = self.warm
            m.submodules.iofabric = iofabric = SimpleFabric(
                [
                    partial_decode(m, bootmem.bus, 11),  # 0x____0000
                    partial_decode(m, uart.bus, 11),  # 0x____1000
                    #partial_decode(m, warm.bus, 11),  # 0x____2000
                ]
            )
            m.submodules.fabric = fabric = SimpleFabric(
                [
                    mainmem.bus,
                    partial_decode(m, iofabric.bus, 12),
                ]
            )
            connect(m, self.cpu.bus, fabric.bus)
        else:
            # New bus !! broken !!
            self.cpu.build(m)

        uart = True
        led = False
        flash = False
        warm_boot = True

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

        if led:
            user = platform.request("led", 0)
            m.d.comb += user.o.eq(self.led.pins[0])

        # # Attach the warmboot
        if warm_boot:
            boot = platform.request("boot", 0)
            m.d.comb += [self.warm.loader.eq(boot.i)]

        return m


from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform

p = TinyFPGABXPlatform()

# 3.3V FTDI connected to the tinybx.
# pico running micro python to run
p.add_resources(
    [
        UARTResource(
            0, rx="A8", tx="B8", attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
        ),
        Resource("boot", 0, Pins("A9", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("user", 0, Pins("H2", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
    ]
)


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
        ra = RustArtifacts(pooter.fabric,folder="bootloader")
        ra.make_bootloader()
    if args.generate:
        ra = RustArtifacts(pooter.fabric,folder="firmware")
        ra.make_firmware()
    
    if args.build:
        p.build(pooter, do_program=True)

# TINYBOOT_UART_ADDR=12288 cargo objcopy --release -- -O binary ../tinybx8k.bin
# MEMORY {
#    PROGMEM (rwx): ORIGIN = 0x2000, LENGTH = 512
#    RAM (rw): ORIGIN = 0x0000, LENGTH = 8192
# }
