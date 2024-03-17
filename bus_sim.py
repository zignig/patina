import argparse

from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth.back import verilog
from amaranth.lib.wiring import *
from amaranth.lib.enum import *

from hapenny.cpu import Cpu
from hapenny.bus import BusPort, partial_decode, SimpleFabric, SMCFabric
from hapenny import *
from hapenny.mem import BasicMemory
from hapenny.gpio import OutputPort
import logging
from rich.logging import RichHandler


import logging

log = logging.getLogger(__name__)


def write_mem(addr, value):
    yield fabric.bus.cmd.payload.addr.eq(addr)
    yield fabric.bus.cmd.payload.data.eq(value & 0xFFFF)
    yield fabric.bus.cmd.payload.lanes.eq(0b11)
    yield fabric.bus.cmd.valid.eq(1)
    yield
    yield fabric.bus.cmd.payload.addr.eq(addr + 1)
    yield fabric.bus.cmd.payload.data.eq(value >> 16)
    yield fabric.bus.cmd.payload.lanes.eq(0b11)
    yield fabric.bus.cmd.valid.eq(1)
    yield
    yield fabric.bus.cmd.payload.lanes.eq(0)
    yield fabric.bus.cmd.valid.eq(0)


def read_mem(addr):
    yield fabric.bus.cmd.payload.addr.eq(addr)
    yield fabric.bus.cmd.payload.lanes.eq(0)
    yield fabric.bus.cmd.valid.eq(1)
    yield
    yield fabric.bus.cmd.payload.addr.eq(addr + 1)
    yield fabric.bus.cmd.valid.eq(1)
    yield
    bottom = yield fabric.bus.resp
    yield
    yield fabric.bus.cmd.valid.eq(0)
    yield
    top = yield fabric.bus.resp
    #print(">>", top, bottom)
    return bottom | (top << 16)


class State(Enum):
    WRITE = 0
    READ = 1


if __name__ == "__main__":
    m = Module()
    mem = BasicMemory(depth=32)
    mem2 = BasicMemory(depth=32, name="second_mem")
    #io = OutputPort(pins=4)
    fabric = SMCFabric([mem, mem2])#, io])
    m.submodules["fabric"] = fabric

    # original fabric
    phase = Signal(State)

    sim = Simulator(m)
    sim.add_clock(1e-6)

    ports = [phase]

    for i in fabric.memory_map.all_resources():
        print(i.path, i.start, i.end)

    print()

    for i in fabric.memory_map.window_patterns():
        print(i)

    size = 2 ** (fabric.memory_map.addr_width )

    def process():
        started = True
        #
        yield phase.eq(State.WRITE)
        for i in range(size):
            yield from write_mem(i*2, i)
        yield phase.eq(State.READ)
        for i in range(size):
            val = yield from read_mem(i*2)
            print(i, hex(val))

    sim.add_sync_process(process)

    with sim.write_vcd(vcd_file="test.vcd", gtkw_file="test.gtkw", traces=ports):
        sim.run()
