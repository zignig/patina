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

    class enableReg(csr.Register,access="rw"):
        enable: csr.Field(csr.action.RW,1)

    class multi(csr.Register,access="rw"):
        first: csr.Field(csr.action.RW,2)
        second: csr.Field(csr.action.RW,2)
        third: csr.Field(csr.action.RW,3)

    def __init__(self, name=None):
        regs = csr.Builder(addr_width=4, data_width=16)
        self.enable = self.enableReg() 
        self.t = self.test_reg(8, 0)
        self.t2 = self.test_reg(16, 0)
        self.t3 = self.test_reg(24,100)
        self.m = self.multi()

        regs.add("enable",self.enable)
        regs.add("test", self.t)
        regs.add("test2", self.t2)
        regs.add("t3",self.t3)
        regs.add("m",self.m)

        self._bridge = csr.Bridge(regs.as_memory_map())

        super().__init__({"bus": In(csr.Signature(addr_width=4, data_width=16))})
        self.bus.memory_map = self._bridge.bus.memory_map

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge
        connect(m, flipped(self.bus), self._bridge.bus)
        # add module logic here
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
        self.addr_bits = 6
        # get widths
        self.dec = csr.Decoder(addr_width=self.addr_bits,data_width=16)
        for i in devices:
            self.dec.add(i.bus,name=uniq_name(i.__class__.__qualname__))
        super().__init__({"bus": In(BusPort(addr=self.addr_bits, data=16))})
        self.dec.bus.memory_map.csr_only = True
        self.memory_map = self.dec.bus.memory_map
        
    
    def elaborate(self, platform):
        m = Module()
