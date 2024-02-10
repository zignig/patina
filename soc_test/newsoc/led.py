from amaranth import *
from amaranth.utils import bits_for
from amaranth.lib import wiring
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib.wiring import In, Out

from amaranth_soc import csr

class Led(wiring.Component):
    led: Signal(1)

    class active(csr.Register,access='rw'):
        led : csr.Field(csr.action.RW,unsigned(1))
    
    def __init__(self):
        rm = csr.RegisterMap()
        self.control = self.active()
        rm.add_register(self.control,name="led")
        self._bridge = csr.Bridge(rm, addr_width=1, data_width=8,name="led")

        super().__init__({
            "bus": In(csr.Signature(addr_width=1, data_width=8))
        })
        self.bus.memory_map = self._bridge.bus.memory_map

    def elaborate(self,platform):
        m = Module()
        m.submodules.bridge = self._bridge

        m.d.comb += [
        ]

        return m
