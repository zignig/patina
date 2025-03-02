# Timer

from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr


class Enable(csr.Register, access="rw"):
    "Enable/Disable the timer"

    def __init__(self):
        super().__init__({"val": csr.Field(csr.action.RW,1)})


class Overflow(csr.Register, access="rw"):
    "Set the overflow value"
    def __init__(self,width):
        super().__init__({"val": csr.Field(csr.action.RW,width)})

class Timer(wiring.Component):

    def __init__(self,width = 32):
        self.width = width

        regs = csr.Builder(addr_width=4, data_width=8)
        self.enable = regs.add("en", Enable())
        self.overflow = regs.add("ovf", Overflow(width))

        self._bridge = csr.Bridge(regs.as_memory_map())
        super().__init__(
            {
                "bus": In(
                    csr.Signature(
                        addr_width=regs.addr_width, data_width=regs.data_width
                    )
                ),
                "irq": Out(unsigned(1)),
            }
        )

        self.bus.memory_map = self._bridge.bus.memory_map

    def elaborate(self, plaform):
        m = Module()
        m.submodules.bridge = self._bridge
        connect(m, flipped(self.bus), self._bridge.bus)

        # the timer
        val = Signal(unsigned(self.width))

        # write the overflow value
        # if m.If( self.overflow.f.)

        # reload the timer if it hits overflow
        with m.If( self.overflow.f.val.data == val):
            m.d.sync += val.eq(0)

        # increment the timer
        with m.If(self.enable.f.val.data == 1 ):
            m.d.sync += val.eq(val+1)

        return m
