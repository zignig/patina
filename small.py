#!/usr/bin/env python

from amaranth import Elaboratable, Module
from amaranth.lib.wiring import connect

from amaranth_boards.resources.interface import UARTResource
from amaranth.build import Attrs


from hapenny.cpu import Cpu
from hapenny.serial import BidiUart
from hapenny.mem import BasicMemory

from patina.generate import *
from patina.fabric_builder import FabricBuilder, BootMem
from patina.warmboot import WarmBoot
from patina.watchdog import Watchdog
from patina.spi import SimpleSPI
from patina.amcsr import Amcsr_bus
from patina.peripheral.timer import Timer
from patina import cli
from patina import log_base
import logging

log = logging.getLogger(__name__)


class Computer(Elaboratable):
    def __init__(self, serial="/dev/ttyUSB0", baud=115200, firmware=None):
        F = 16e6  # Hz

        super().__init__()

        # cli uses these to connect
        self.serial = serial
        self.baud = baud
        self.firmware = firmware

        # some csr style devices to attach the Amcsr_bus
        self.timer = timer = Timer()
        # CSR bus bridge ( 8 bit databus)
        self.csr = Amcsr_bus([timer])

        # RAM should be at the top 
        self.mainmem = mainmem = BasicMemory(depth=512 * 10)  # 16bit cells
        # serial bootloader
        self.bootmem = bootmem = BootMem()  # one bram , auto build

        self.warmboot = warmboot = WarmBoot()
        self.watchdog = watchdog = Watchdog()

        # this is board specific , depends on the flash chip
        self.spi = spi = SimpleSPI(start_addr=50000, flash_size=1024)

        # uart connection to the outside world
        self.bidi = BidiUart(baud_rate=baud, oversample=4, clock_freq=F)

        # create the list of devices
        devices = [
            self.mainmem,
            self.bootmem,
            self.bidi,
            self.warmboot,
            self.watchdog,
            self.spi,
            self.csr
        ]

        self.fabric = fabric = FabricBuilder(devices)

        self.cpu = Cpu(reset_vector=fabric.reset_vector, addr_width=fabric.addr_width)

    def elaborate(self, platform):
        m = Module()
        
        # Add the CPU
        m.submodules.cpu = self.cpu

        # Add the fabric
        m.submodules.fabric = self.fabric

        # Connect the cpu to the fabric
        connect(m, self.cpu.bus, self.fabric.bus)

        uart = True
        flash = True

        if uart:
            uartpins = platform.request("uart", 0)
            self.bidi.bind(m, uartpins)

        if flash:
            spi_pins = platform.request("spi_flash_1x")
            m.d.comb += [
                # peripheral to outside world
                spi_pins.clk.o.eq(self.spi.clk),
                spi_pins.cs.o.eq(~self.spi.cs),
                spi_pins.copi.o.eq(self.spi.copi),
                self.spi.cipo.eq(spi_pins.cipo.i),
            ]

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

    pooter = Computer(
        serial="/dev/ttyUSB0", baud=115200, firmware=["firmware", "console"]
    )

    cli.run(platform, pooter)
