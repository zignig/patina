import itertools
import random
import argparse

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.build import ResourceError, Resource, Pins, Attrs
from amaranth_boards.test.blinky import Blinky
from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform

from hapenny import StreamSig
from hapenny.cpu16 import Cpu
from hapenny.bus import BusPort, SimpleFabric, partial_decode
from hapenny.gpio import OutputPort

RAM_WORDS = 256 * 16 # 8Kb
BUS_ADDR_BITS = (RAM_WORDS - 1).bit_length()

# from https://github.com/zignig/patina 
# 00000000 <_start>:
#        0:       auipc   sp, 2
#        4:       mv      sp, sp
#        8:       j       0xc <__start_rust>

# 0000000c <__start_rust>:
#        c:       li      a3, 0
#       10:       li      a0, -1
#       14:       lui     a1, 2
#       18:       li      a2, 1
#       1c:       nop
#       20:       addi    a3, a3, 1
#       24:       bne     a3, a0, 0x1c <__start_rust+0x10>
#       28:       sw      zero, 4(a1)
#       2c:       li      a3, -1
#       30:       nop
#       34:       addi    a3, a3, -1
#       38:       bnez    a3, 0x30 <__start_rust+0x24>
#       3c:       sw      a2, 4(a1)
#       40:       j       0x1c <__start_rust+0x10>

# 00000044 <DefaultInterruptHandler>:
#       44:       ret

program = [5921, 0, 4865, 256, 
           28416, 16384, 37638, 0, 
           4869, 61695, 46885, 0, 
           4870, 4096, 4864, 0, 
           37766, 5632, 58268, 42750, 
           9122, 1280, 37638, 61695, 
           4864, 0, 37766, 63231, 
           58268, 1790, 9122, 50432, 
           28656, 57341, 26496, 0]

class TestMemory(Component):
    bus: In(BusPort(addr = BUS_ADDR_BITS, data = 16))

    def __init__(self, contents):
        super().__init__()

        self.m = Memory(
            width = 16,
            depth = RAM_WORDS,
            name = "testram",
            init = contents,
        )

    def elaborate(self, platform):
        m = Module()

        m.submodules.m = self.m

        rp = self.m.read_port(transparent = False)
        wp = self.m.write_port(granularity = 8)

        m.d.comb += [
            rp.addr.eq(self.bus.cmd.payload.addr[1:]),
            rp.en.eq(self.bus.cmd.valid & (self.bus.cmd.payload.lanes == 0)),

            wp.addr.eq(self.bus.cmd.payload.addr[1:]),
            wp.data.eq(self.bus.cmd.payload.data),
            wp.en[0].eq(self.bus.cmd.valid & self.bus.cmd.payload.lanes[0]),
            wp.en[1].eq(self.bus.cmd.valid & self.bus.cmd.payload.lanes[1]),

            # Nothing causes this memory to stop being available.
            self.bus.cmd.ready.eq(1),
        ]

        # Delay the read enable signal by one cycle to use as output valid.
        # TODO this isn't really correct and ignores ready.
        delayed_read = Signal(1)
        m.d.sync += delayed_read.eq(rp.en)

        m.d.comb += [
            self.bus.resp.valid.eq(delayed_read),
            self.bus.resp.payload.eq(rp.data),
        ]

        return m


class Test(Elaboratable):
    def __init__(self, has_interrupt = None):
        super().__init__()

        self.has_interrupt = has_interrupt

    def elaborate(self, platform):
        m = Module()
        m.submodules.cpu = cpu = Cpu(
            addr_width = BUS_ADDR_BITS + 1 + 1,
            has_interrupt = self.has_interrupt,
        )
        random.seed("omglol")
        m.submodules.mem = mem = TestMemory(program)
        m.submodules.port = port = OutputPort(1)
        m.submodules.fabric = fabric = SimpleFabric([
            mem.bus,
            partial_decode(m, port.bus, BUS_ADDR_BITS),
        ])

        connect(m, cpu.bus, fabric.bus)

        def get_all_resources(name):
            resources = []
            for number in itertools.count():
                try:
                    resources.append(platform.request(name, number))
                except ResourceError:
                    break
            return resources

        leds     = [res.o for res in get_all_resources("led")]
        m.d.comb += [
            leds[0].eq(port.pins),
        ]
        if self.has_interrupt is not None:
            irq = platform.request("irq", 0)
            m.d.comb += [
                cpu.irq.eq(irq.i),
            ]

        return m

parser = argparse.ArgumentParser(
    prog = "tinybx16",
    description = "Script for synthesizing image for HX1K",
)
parser.add_argument('-i', '--interrupt-model', help = 'which interrupt model to use', required = False, choices = ['m', 'fast'])
args = parser.parse_args()

p = TinyFPGABXPlatform()
p.resources["irq", 0] = Resource("irq", 0, Pins("J1", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS"))
#p.build(Test(has_interrupt = args.interrupt_model))
p.build(Test(has_interrupt = args.interrupt_model),do_program=True)

