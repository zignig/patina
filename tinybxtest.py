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
from patina.watchdog import Watchdog

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
bootloader = Path("boot12k.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)

log.info("image_size {}", 2 ** (len(boot_image)).bit_length())


class Computer(Elaboratable):
    def __init__(self):
        F = 16e6  # Hz
        super().__init__()

        mainmem = BasicMemory(depth=512 * 12)  # 16bit cells
        bootmem = BootMem(boot_image)

        # these are attached to self so they can be altered in elaboration.

        self.bidi = BidiUart(baud_rate=115200, oversample=4, clock_freq=F)
        self.led = OutputPort(1, read_back=True)
        self.input = InputPort(5)
        self.spi = SimpleSPI(fifo_depth=512)
        self.warm = WarmBoot()
        self.watchdog = Watchdog()

        devices = [
            mainmem,
            bootmem,
            self.bidi,
            self.warm,
            self.led,
            self.input,
            self.spi,
            self.watchdog
        ]

        self.fabric = fabric = FabricBuilder(devices)

        # TODO perhaps this should be in the interior.
        self.cpu = Cpu(
            reset_vector=fabric.reset_vector, addr_width=fabric.addr_width
        )


    def elaborate(self, platform):
        m = Module()

        # This creates and binds all the devices
        old = False
        if old:
            # cliffs default bus layout
            log.warning("Build  the bus")
            log.warning("")
            # old style bus
            m.submodules.cpu = self.cpu
            m.submodules.mainmem = mainmem = self.mainmem
            m.submodules.mem = bootmem = self.bootmem
            m.submodules.uart = uart = self.bidi
            m.submodules.warm = warm = self.warm
            m.submodules.led = led = self.led
            m.submodules.input = input = self.input

            bus_width = self.fabric.decoder_width

            m.submodules.fabric = fabric = SimpleFabric(
                [
                    partial_decode(m, mainmem.bus, bus_width),
                    partial_decode(m, bootmem.bus, bus_width),
                    partial_decode(m, uart.bus, bus_width),
                    partial_decode(m, warm.bus, bus_width),
                    partial_decode(m, led.bus, bus_width),
                    partial_decode(m, input.bus, bus_width),
                    # partial_decode(m,spi.bus,bus_width)
                ]
            )
            connect(m, self.cpu.bus, fabric.bus)
        else:
            # TODO clean me.
            # Add the CPU
            m.submodules.cpu = self.cpu
            # Add the fabric
            m.submodules.fabric = self.fabric
            # Bind the fabric (weird semantics in elaborate)
            self.fabric.bind(m)
            # Connect the cpu and the fabric
            connect(m, self.cpu.bus, self.fabric.bus)

        uart = True
        led = True
        flash = True
        warm_boot = True
        input_pins = False

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

        if input_pins:
            pin1 = platform.request("boot", 0)
            pin2 = platform.request("user", 0)

            boot_post_sync = Signal()

            m.submodules.boot_sync = amaranth.lib.cdc.FFSynchronizer(
                i=pin1.i,
                o=boot_post_sync,
                o_domain="sync",
                init=1,
                stages=2,
            )
            m.d.comb += self.input.pins[0].eq(boot_post_sync)
            m.d.comb += self.input.pins[1].eq(pin2.i)

        # # Attach the warmboot
        if warm_boot:
            #boot = platform.request("boot", 0)
            m.d.comb += self.warm.external.eq(self.watchdog.activate)

        return m


from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform

p = TinyFPGABXPlatform()

# 3.3V FTDI connected to the tinybx.
# pico running micro python to run external comms
p.add_resources(
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

# TINYBOOT_UART_ADDR=12288 cargo objcopy --release -- -O binary ../tinybx8k.bin
# MEMORY {
#    PROGMEM (rwx): ORIGIN = 0x2000, LENGTH = 512
#    RAM (rw): ORIGIN = 0x0000, LENGTH = 8192
# }
