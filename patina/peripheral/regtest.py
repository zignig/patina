# Timer

from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr


# register with no sub vals 
def nood_reg(width):
    return csr.Register(csr.Field(csr.action.RW,width),access="rw")

class RegTest(wiring.Component):

    def __init__(self, width=32):
        self.width = width

        regs = csr.Builder(addr_width=4, data_width=8)
        self.u8 = ru8 = regs.add('u8',nood_reg(8))
        self.u8target = ru8 = regs.add('u8target',nood_reg(8))
        self.u16 = ru16 = regs.add('u16',nood_reg(16))
        self.u32 = ru32 = regs.add('u32',nood_reg(32))

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
        return m
