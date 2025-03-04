from amaranth import *
from amaranth.lib.wiring import *

from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

# A bridge from the hapenny bus an 8 bit csr bus
# ( over troubled water)
# harder than it loogs 

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
        self.dec = csr.Decoder(addr_width=self.addr_bits, data_width=8)
        for i in devices:
            name = None
            if hasattr(i, "name"):
                name = uniq_name(i.name)
            else:
                name = uniq_name(i.__class__.__qualname__)
            i.name = name
            self.dec.add(i.bus, name=name)

        super().__init__({"bus": In(BusPort(addr=self.addr_bits, data=16))})

        # INFO , the mapper uses this for svd generation.

        self.dec.bus.memory_map.csr_only = True
        self.memory_map = self.dec.bus.memory_map

    def elaborate(self, platform):
        m = Module()
        # connect the csr bus
        m.submodules.csr_bus = self.dec
        # connect the devices
        for dev in self.devices:
            m.submodules[dev.name] = dev
        # connect the bus

        # bus cmd shorthand
        cmd = self.bus.cmd

        # register the bus response
        # read_data = Signal(16)  # it expects one cycle of read latency
        # m.d.sync += self.bus.resp.eq(read_data)

        # PROBLEM !!!
        # The cpu is 32bit , the bus is 16bit and the csr is 8 bits.
        #
        # The bus does 16 bit cycle reads and write, however it uses
        # lanes to specify the which byte needs to write
        #
        # The biggest problem is that for a reads and writes need two
        # transactions for each read or write
        #
        # the writes have some lane items for bytes , but reads need to
        # get both bytes every time and they are selected inside the cpu
        # there may not be enough cycles.
        # state machine

        # d = Signal(1)
        # first_address = Signal(16)
        # second_address = Signal(16)
        # with m.FSM():
        #     with m.State("WAIT"):
        #         with m.If(cmd.valid):
        #             m.d.sync += d.eq(1)
        #             m.next = "START"

        #             # m.d.sync += [
        #             #     self.dec.bus.w_stb.eq(0),
        #             #     first_address.eq(cmd.payload.addr),
        #             # ]

        #     with m.State("START"):
        #         m.d.sync += [
        #             # drop the first write
        #             self.dec.bus.w_stb.eq(1),
        #             # set the next address
        #             self.dec.bus.addr.eq(first_address + 1),
        #             self.dec.bus.w_data.eq(cmd.payload.data)
        #         ]
        #         m.next = "FIRST"

        #     with m.State("FIRST"):
        #         m.d.sync += [self.dec.bus.w_stb.eq(0)]
        #         m.next = "SECOND"

        #     with m.State("SECOND"):
        #         m.d.sync += d.eq(1)
        #         m.next = "WAIT"

        ## read
        with m.If(cmd.valid & (cmd.payload.lanes == 0)):
            m.d.comb += [
                self.dec.bus.addr.eq(cmd.payload.addr),
                self.dec.bus.r_stb.eq(1),
                self.bus.resp.eq(self.dec.bus.r_data),
            ]

        ## write
        with m.If(cmd.valid & (cmd.payload.lanes.any())):
            m.d.comb += [
                self.dec.bus.addr.eq(cmd.payload.addr),
                self.dec.bus.w_stb.eq(1),
                self.dec.bus.w_data.eq(cmd.payload.data),
            ]

        return m
