import argparse

from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth.back import verilog
from amaranth.lib.wiring import *
from amaranth.lib.enum import *

from hapenny.cpu import Cpu
from hapenny.bus import BusPort, partial_decode, SimpleFabric
from hapenny import *
from hapenny.mem import BasicMemory

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("computer")
log.setLevel(logging.DEBUG)

class TestPhase(Enum):
    INIT = 0
    SETUP = 1
    RUN = 2
    CHECK = 3

class TestMemory(BasicMemory):
    def __init__(self, contents,name):
        super().__init__(
            contents = contents,
            depth = 256,
            name = name
        )

        # make a second bus port
        self.inspect = BusPort(
            addr = self.bus.cmd.payload.addr.shape().width + 1,
            data = 16,
        ).flip().create()

    def elaborate(self, platform):
        m = super().elaborate(platform)

        # Create a second read/write port.
        inspect_rp = self.m.read_port(transparent = False)
        inspect_wp = self.m.write_port(granularity = 8)

        m.d.comb += [
            inspect_rp.addr.eq(self.inspect.cmd.payload.addr[1:]),
            inspect_rp.en.eq(self.inspect.cmd.valid &
                             (self.inspect.cmd.payload.lanes == 0)),

            inspect_wp.addr.eq(self.inspect.cmd.payload.addr[1:]),
            inspect_wp.data.eq(self.inspect.cmd.payload.data),
            inspect_wp.en[0].eq(self.inspect.cmd.valid &
                                self.inspect.cmd.payload.lanes[0]),
            inspect_wp.en[1].eq(self.inspect.cmd.valid &
                                self.inspect.cmd.payload.lanes[1]),

            self.inspect.resp.eq(inspect_rp.data),
        ]

        return m

def halt():
    yield uut.halt_request.eq(1)
    attempts = 0
    while (yield uut.halted) == 0:
        attempts += 1
        if attempts > 40:
            raise Exception("CPU didn't halt after 40 cycles")
        yield
#        yield Settle()

def resume():
    yield uut.halt_request.eq(0)
    attempts = 0
    while (yield uut.halted) == 1:
        attempts += 1
        if attempts > 40:
            raise Exception("CPU didn't resume after 40 cycles")
        yield
#        yield Settle()

def single_step():
    yield from resume()
    start = yield cycle_counter
    # do not generate halt during fetch state
    yield
    yield from halt()
    # Subtract 4 here to not count the fetch cycle to refill the pipeline.
    return (yield cycle_counter) - 4 - start

def write_ureg(reg, value):
    yield uut.debug.reg_write.payload.reg.eq(reg)
    yield uut.debug.reg_write.payload.value.eq(value)
    yield uut.debug.reg_write.valid.eq(1)
    yield
    yield uut.debug.reg_write.valid.eq(0)

def write_reg(reg, value):
    yield from write_ureg(reg, value & 0xFFFF)
    yield from write_ureg(reg | 0x20, value >> 16)

def read_ureg(reg):
    yield uut.debug.reg_read.payload.eq(reg)
    yield uut.debug.reg_read.valid.eq(1)
    yield
    yield uut.debug.reg_read.valid.eq(0)
#    yield Settle()
    return (yield uut.debug.reg_value)

def read_reg(reg):
    bottom = yield from read_ureg(reg)
    top = yield from read_ureg(reg | 0x20)
    return bottom | (top << 16)

def write_pc(value):
    yield uut.debug.pc_write.payload.eq(value)
    yield uut.debug.pc_write.valid.eq(1)
    yield
    yield uut.debug.pc_write.valid.eq(0)

def read_pc():
#    yield Settle()
    return (yield uut.debug.pc)

def write_mem(addr, value):
    yield uut.bus.cmd.payload.addr.eq(addr)
    yield uut.bus.cmd.payload.data.eq(value & 0xFFFF)
    yield uut.bus.cmd.payload.lanes.eq(0b11)
    yield uut.bus.cmd.valid.eq(1)
    print(addr,value)
    yield
    yield uut.bus.cmd.payload.addr.eq(addr + 2)
    yield uut.bus.cmd.payload.data.eq(value >> 16)
    yield uut.bus.cmd.payload.lanes.eq(0b11)
    yield uut.bus.cmd.valid.eq(1)
    yield
    yield uut.bus.cmd.payload.lanes.eq(0)
    yield uut.bus.cmd.valid.eq(0)

def read_mem(addr):
    yield uut.bus.cmd.payload.addr.eq(addr)
    yield uut.bus.cmd.payload.lanes.eq(0)
    yield uut.bus.cmd.valid.eq(1)
    yield
    yield uut.bus.cmd.payload.addr.eq(addr + 2)
    yield uut.bus.cmd.valid.eq(1)
    yield Settle()
    bottom = yield uut.bus.resp
    yield
    yield uut.bus.cmd.valid.eq(0)
    yield Settle()
    top = yield uut.bus.resp

    return bottom | (top << 16)

def test_inst(name, inst, *, before = {}, after = {}, stop_after = None):
    if args.filter is not None:
        if args.filter not in name:
            return
    if args.trace:
        print(f"{name} ... ")
    else:
        print(f"{name} ... ", end='')
    yield phase.eq(TestPhase.SETUP)
    for r in range(1, 32):
        if r not in before:
            yield from write_reg(r, 0xCAFEF00D)

    start_address = 0

    for key, value in before.items():
        if isinstance(key, int):
            yield from write_reg(key, value)
        elif isinstance(key, str) and key[0] == '@':
            yield from write_mem(int(key[1:], 16), value)
        elif key == 'PC' or key == 'pc':
            yield from write_pc(value)
            start_address = value
        else:
            raise Exception(f"unexpected before key: {key}")

    if isinstance(inst, int):
        instruction_count = 1
        yield from write_mem(start_address, inst)
    elif isinstance(inst, list):
        instruction_count = len(inst)
        for (i, word) in enumerate(inst):
            yield from write_mem(start_address + 4 * i, word)
    else:
        raise Exception(f"invalid instruction value: {inst}")

    yield from write_pc(start_address)

    yield phase.eq(TestPhase.RUN)
    cycle_count = 0
    if stop_after is not None:
        yield from resume()
        while True:
            cycle_count += 1
            pc = yield from read_pc()
            if pc == stop_after:
                yield from halt()
                break
            yield
    else:
        for i in range(instruction_count):
            cycle_count += yield from single_step()
    yield

    yield phase.eq(TestPhase.CHECK)
    try:
        for key, value in after.items():
            if isinstance(key, int):
                actual = yield from read_reg(key)
                if value is not None:
                    assert actual == value, \
                            f"r{key} should be 0x{value:08x} but is 0x{actual:08x}"
                else:
                    print(f"r{key} (unconstrained) is 0x{actual:x}")
            elif isinstance(key, str) and key[0] == '@':
                addr = int(key[1:], 16)
                actual = yield from read_mem(addr)
                assert actual == value, \
                        f"M[0x{addr:x}] should be 0x{value:x} but is 0x{actual:x}"
            elif key == 'PC' or key == 'pc':
                actual = yield from read_pc()
                assert actual == value, \
                        f"PC should be 0x{value:x} but is 0x{actual:x}"
            else:
                raise Exception(f"unexpected after key: {key}")
        for r in range(1, 32):
            if r not in after:
                if r in before:
                    expected = before[r]
                else:
                    expected = 0xDEADBEEF
                actual = yield from read_reg(r)
                assert actual == expected, \
                    f"r{r} should not have changed but is now 0x{actual:x}"
        if 'PC' not in after:
            actual = yield from read_pc()
            value = start_address + instruction_count * 4
            assert actual == value, \
                    f"PC should be 0x{value:x} but is 0x{actual:x}"




    except Exception as e:
        raise Exception(f"test case {name} failed due to above exception") from e

    print(f"({cycle_count} cyc) PASS")

parser = argparse.ArgumentParser(
    prog = "slip-cpu",
    description = "Test bench for 16-bit model",
)
args = parser.parse_args()

if __name__ == "__main__":
    m = Module()
    uut = Cpu(counters = True,addr_width=32)

    mem = TestMemory([],name="mem")
    mem2 = TestMemory([],name="mem2")
    uut.add_device([mem,mem2])
    uut.build(m)
    uut.show()

    phase = Signal(TestPhase)
    cycle_counter = Signal(32)
    m.d.sync += cycle_counter.eq(cycle_counter + 1)

    # m.submodules.bus = fabric = SimpleFabric([
    #     partial_decode(m, mem.bus, 31),
    # ])

    # connect(m, uut.bus, fabric.bus)

    ports = [
        # phase,
        # uut.halt_request,
        # uut.halted,
        # uut.s.onehot_state,
        # uut.ew.full,
        # uut.rf.read_cmd.valid,
        # uut.rf.read_cmd.payload,
        # uut.rf.write_cmd.valid,
        # uut.rf.write_cmd.payload.reg,
        # uut.rf.write_cmd.payload.value,
        # uut.bus.cmd.valid,
        # uut.bus.cmd.payload.addr,
        # uut.bus.cmd.payload.data,
        # uut.bus.cmd.payload.lanes,
        # uut.bus.resp,
    ]

    ports = []

    # verilog_src = verilog.convert(m, ports=ports)
    # with open("sim-cpu.v", "w") as v:
    #     v.write(verilog_src)

    started = False
    stopping = False

    sim = Simulator(m)
    sim.add_clock(1e-6)

    def process():
        global stopping
        global started
        started = True
        for i in range(50):
            yield from write_mem(i,i*1024)
            yield from write_pc(i)
            yield from single_step()
            yield
            yield
            yield
        yield
        yield
        yield
        stopping = True

    sim.add_sync_process(process)

    with sim.write_vcd(vcd_file="test.vcd", gtkw_file="test.gtkw", traces=ports):
        sim.run()
