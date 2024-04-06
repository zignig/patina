from amaranth import *
from amaranth.utils import bits_for
from amaranth.lib import wiring
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib.wiring import In, Out

from amaranth_soc import csr


class Counter(wiring.Component):
    bus: In(csr.Signature(addr_width=2, data_width=32))

    class enable(csr.Register, access="rw"):
        value: csr.Field(csr.action.RW, unsigned(1))

    class counter(csr.Register, access="r"):
        value: csr.Field(csr.action.R, unsigned(8))

    class overflow(csr.Register,access="rw"):
        value: csr.Field(csr.action.RW,unsigned(8))


    class cfg(csr.Register,access="rw"):
        inter: csr.Field(csr.action.RW,unsigned(1))
        ovf_inter: csr.Field(csr.action.RW,unsigned(1))
        oneshot: csr.Field(csr.action.RW,unsigned(1))
    
    def __init__(self):
        self._enable = self.enable()
        self._counter = self.counter()
        self._overflow = self.overflow()
        self._config = self.cfg()

        regs = csr.Builder(name="counter", addr_width=2, data_width=32,granularity=8)
        regs.add("enable", self._enable)
        regs.add("counter", self._counter)
        regs.add("overflow",self._overflow)
        regs.add("config",self._config)

        self._csr_bridge = csr.Bridge(regs.as_memory_map())
        super().__init__()

        self.bus.memory_map = self._csr_bridge.bus.memory_map

    def elaborate(self, platform):
        m = Module()
        m.d.comb += []

        return m
