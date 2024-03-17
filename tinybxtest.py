import itertools
import argparse
import struct
from pathlib import Path

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.build import ResourceError, Resource, Pins, Attrs
from amaranth_boards.test.blinky import Blinky
from amaranth_boards.resources.interface import UARTResource
from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform
import amaranth.lib.cdc

from hapenny import StreamSig
from hapenny.cpu import Cpu
from hapenny.bus import BusPort, SimpleFabric, partial_decode, SMCFabric
from hapenny.serial import BidiUart
from hapenny.mem import BasicMemory, BootMem
from hapenny.gpio import OutputPort, InputPort

from warmboot import WarmBoot
from twiddler import Twiddle
from spi import SimpleSPI

from generate import * 

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("computer")
log.setLevel(logging.WARNING)


# tiny-bootloader is written in a high-level language and needs to have a stack,
RAM_WORDS = 256
RAM_ADDR_BITS = (RAM_WORDS - 1).bit_length()
BUS_ADDR_BITS = RAM_ADDR_BITS + 1

bootloader = Path("tinybx8k.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)

print("image_size",2**(len(boot_image)).bit_length())

class Computer(Elaboratable):
    def __init__(self):
        F = 16e6  # Hz
        super().__init__()
        self.cpu = Cpu(reset_vector=4096, addr_width=15)

        mainmem = BasicMemory(depth=256 * 16)
        bootmem = BootMem(boot_image)
        # these are attached to self so they can be altered in elaboration.
        self.bidi = BidiUart(baud_rate=57600, oversample=8, clock_freq=F)

        self.led = OutputPort(1, read_back=True)
        self.input = InputPort(1)

        self.spi = SimpleSPI(fifo_depth=512)

        mini = False

        if not mini:
            self.cpu.add_device(
                [mainmem, bootmem, self.bidi, self.spi, self.led, self.input]
            )
        else:
            self.cpu.add_device([bootmem, self.led])

    def elaborate(self, platform):
        m = Module()

        self.cpu.build(m)

        uart = True
        led = True
        flash = True
        warm_boot = True
        print(self.cpu.active)
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
            m.submodules.warm = warm = WarmBoot()

            boot = platform.request("boot", 0)
            m.d.comb += [warm.loader.eq(boot.i)]

        return m


p = TinyFPGABXPlatform()
# 3.3V FTDI connected to the tinybx.
# pico running micro python to run
p.add_resources(
    [
        UARTResource(
            0, rx="A8", tx="B8", attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
        ),
        Resource("boot", 0, Pins("A9", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # Resource("user", 0, Pins("H2", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Patina Running on tinybx",
        description="riscv32i mini soc",
        epilog="awesome!",
    )

    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("-b", "--build", action="store_true")
    parser.add_argument("-m", "--mapping", action="store_true")
    parser.add_argument("-g", "--generate", action="store_true")
    

    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    log.info("Building Patina")
    log.debug("Debug mode on")

    pooter = Computer()

    if args.verbose:
        pooter.cpu.show()
        pooter.memory_map = pooter.cpu.memory_map
    if args.generate:
        pooter.cpu.create_map()
        pooter.memory_map = pooter.cpu.memory_map
        memx = GenRust(pooter.cpu)
        #f = open("memory.x",'w')
        memx.generate_memory_x()

    if args.build:
        p.build(pooter, do_program=True)

# TINYBOOT_UART_ADDR=12288 cargo objcopy --release -- -O binary ../tinybx8k.bin
# MEMORY {
#    PROGMEM (rwx): ORIGIN = 0x2000, LENGTH = 512
#    RAM (rw): ORIGIN = 0x0000, LENGTH = 8192
# }
