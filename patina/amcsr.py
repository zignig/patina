from amaranth import *
from amaranth.lib.wiring import *

from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort


class testp(Component):
    class test_reg(csr.Register, access="rw"):
        def __init__(self, width, init):
            super().__init__(
                {
                    "val": csr.Field(csr.action.RW, width, init=init),
                }
            )

    def __init__(self, name=None):
        regs = csr.Builder(addr_width=4, data_width=16)
        self.t = self.test_reg(8, 0)
        self.t2 = self.test_reg(8, 0)
        regs.add("test", self.t)
        regs.add("test2", self.t2)
        self._bridge = csr.Bridge(regs.as_memory_map())

        super().__init__({"bus": In(csr.Signature(addr_width=4, data_width=16))})
        self.bus.memory_map = self._bridge.bus.memory_map

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge
        return m


class Amcsr_bus(Component):
    name = "csr_bus"

    def __init__(self, devices):
        name_dict = {}

        def uniq_name(name):
            if name in name_dict:
                name_dict[name] += 1
                return name + "_" + str(name_dict[name])
            else:
                name_dict[name] = 0
                return name

        # for fixed for now
        self.name = uniq_name(self.__class__.__qualname__)
        self.devices = devices
        self.addr_bits = 5
        # get widths
        self.memory_map = mm = MemoryMap(addr_width=self.addr_bits, data_width=16)
        # temp for svg generation
        mm.csr_only = True
        self.mult = csr.Multiplexer(mm)
        for i in devices:
            mm.add_resource(i, name=uniq_name("test"), size=4)
        super().__init__({"bus": In(BusPort(addr=self.addr_bits, data=16))})

    def elaborate(self, platform):
        m = Module()
