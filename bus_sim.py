import argparse

from pathlib import Path
import struct


from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth.back import verilog
from amaranth.lib.wiring import *
from amaranth.lib.enum import *

from hapenny.cpu import Cpu
from hapenny.bus import BusPort, partial_decode, SimpleFabric, SMCFabric
from hapenny import *
from hapenny.mem import BasicMemory, BootMem
from hapenny.gpio import OutputPort
import logging
from rich.logging import RichHandler

from spi import SimpleSPI

import logging

log = logging.getLogger(__name__)


from riscv_assembler.convert import AssemblyConverter as AC

asm = """
nop
nop
nop
nop
nop
nop


li a0, 8192 # control register 
li a1, 8194 # data register 

li a5, 36865  # 0b1001000000000001 # write 
ori a5, a5, 2 # 1 byte
sw a5, 0(a0)

li a7, 20
tx_wait:
    addi a7,a7,-1
    bge x0,a7, tx_wait

li a5,1024
sw a5, 0(a1)



# Change to read register
li a5, 5
sw a5, 0(a0) # read

lw a6, 0(a1)
lw a6, 0(a1)
lw a6, 0(a1)
lw a6, 0(a1)
lw a6, 0(a1)

# spin
loop:
j loop

"""

cnv = AC(output_mode="a", hex_mode=True)
data = cnv(asm)

boot_file = []
for i in data:
    as_num = int(i, base=16)
    lower = as_num & 0xFFFF
    upper = as_num >> 16
    # print(hex(as_num))
    print(hex(upper), hex(lower))
    boot_file.append(lower)
    boot_file.append(upper)

print(boot_file)


RAM_WORDS = 256
RAM_ADDR_BITS = (RAM_WORDS - 1).bit_length()
BUS_ADDR_BITS = RAM_ADDR_BITS + 1

bootloader = Path("tinybx8k.bin").read_bytes()
boot_image = struct.unpack("<" + "h" * (len(bootloader) // 2), bootloader)





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
    # print(">>", top, bottom)
    return bottom | (top << 16)


class State(Enum):
    WRITE = 0
    READ = 1


if __name__ == "__main__":
    m = Module()
    mem = BasicMemory(depth=512)
    #mem2 = BasicMemory(depth=32, name="second_mem")
    io = OutputPort(pins=4)
    bootmem = BootMem(boot_image,image_size=512)
    
    # fabric = SMCFabric([mem, mem2])#, io])
    flash = SimpleSPI()
    cpu = Cpu(addr_width=14)
    # cpu.add_device([mem3, mem2, mem, io, flash])
    # cpu.build(m)
    m.submodules.cpu = cpu
    m.submodules.flash = flash
    m.submodules.mem = mem
    m.submodules.bootmem = bootmem
    m.submodules.io = io

    m.submodules.iofabric = iofabric = SimpleFabric(
        [
            partial_decode(m, bootmem.bus, 11),  # 0x____1000
            partial_decode(m, mem.bus, 11),  # 0x____0000
            partial_decode(m,flash.bus,11)  # 0x____2000
        ]
    )
    connect(m, cpu.bus, iofabric.bus)

    # original fabric
    phase = Signal(State)

    sim = Simulator(m)
    sim.add_clock(1e-6)

    ports = [phase]

    # for i in cpu.memory_map.all_resources():
    #     print(i.path, i.start << 1, i.end << 1)

    # print()

    # for i in cpu.memory_map.window_patterns():
    #     print(i)

    # size = 2 ** (cpu.memory_map.addr_width - 1)
    # size = 1024
    # print(size)
    size = 1024
    def process():
        started = True
        #
        for i in range(size):
            yield
            if (i % 64) == 0 :
                print(i,size)
        # yield phase.eq(State.WRITE)
        # for i in range(size):
        #     yield from write_mem(i*2, i)
        #     print(i, hex(i))
        # yield phase.eq(State.READ)
        # for i in range(size):
        #     val = yield from read_mem(i*2)
        #     print(i, hex(val))

    sim.add_sync_process(process)

    with sim.write_vcd(vcd_file="test.vcd", gtkw_file="test.gtkw", traces=ports):
        sim.run()
