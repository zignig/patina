from amaranth import *
from amaranth.lib.wiring import *

from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

# this is some testing with a view to converting hapeeny to a csr bus internally.

class enableReg(csr.Register,access="rw"):
    enable: csr.Field(csr.action.RW,1)

class toggleReg(csr.Register,access="rw"):
    toggle: csr.Field(csr.action.RW,64)

# csr periperal test 
class compl(Component):
    def __init__(self,name=None):
        regs = csr.Builder(addr_width=4, data_width=8)
        regs.add("enable",enableReg())
        toggle = csr.Register(csr.Field(csr.action.RW,64),access="rw")
        regs.add("toggle",toggleReg())

        self._bridge = csr.Bridge(regs.as_memory_map())

        super().__init__({"bus": In(csr.Signature(addr_width=4, data_width=8))})
        self.bus.memory_map = self._bridge.bus.memory_map

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge
        connect(m, flipped(self.bus), self._bridge.bus)
        # add module logic here
        return m
    
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
        if name:
            self.name = name
        regs = csr.Builder(addr_width=4, data_width=8)
        self.enable = self.enableReg() 
        self.t = self.test_reg(8, 0)
        self.t2 = self.test_reg(16, 0)
        self.m = self.multi()

        regs.add("enable",self.enable)
        regs.add("test", self.t)
        regs.add("test2", self.t2)
        regs.add("action",self.m)

        self._bridge = csr.Bridge(regs.as_memory_map())

        super().__init__({"bus": In(csr.Signature(addr_width=4, data_width=8))})
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

        self.name = uniq_name(self.__class__.__qualname__)
        self.devices = devices
        # for fixed for now
        self.addr_bits = 10
        # get widths
        self.dec = csr.Decoder(addr_width=self.addr_bits,data_width=8)
        for i in devices:
            name = None
            if hasattr(i,"name"):
                name = uniq_name(i.name)
            else:
                name=uniq_name(i.__class__.__qualname__)
            self.dec.add(i.bus,name=name)
    
        super().__init__({"bus": In(BusPort(addr=self.addr_bits, data=16))})
        self.dec.bus.memory_map.csr_only = True
        self.memory_map = self.dec.bus.memory_map
        
    
    def elaborate(self, platform):
        m = Module()
        # connect the devices
        for dev in self.devices:
             m.submodules += dev
        # connect the bus
        # bus cmd shorthand
        cmd = self.bus.cmd

        # register the bus response
        read_data = Signal(16)  # it expects one cycle of read latency
        m.d.sync += self.bus.resp.eq(read_data)
        ## read 
        with m.If(cmd.valid & (cmd.payload.lanes == 0 )):
            m.d.comb += [
                self.dec.bus.addr.eq(cmd.payload.addr),
                self.dec.bus.r_stb.eq(1),
                read_data.eq(self.dec.bus.r_data),
            ],
        ## write
        with m.If(cmd.valid &  (cmd.payload.lanes.any() )):
            m.d.comb += [
                self.dec.bus.addr.eq(cmd.payload.addr),
                self.dec.bus.w_stb.eq(1),
                self.dec.bus.w_data.eq(cmd.payload.data)
            ]
        
        return m