from amaranth import *
from amaranth.utils import bits_for
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib import data, wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap
from amaranth_soc.csr import Field, action

from gensvd import GenSVD
from gen_rust import GenRust
from serial import AsyncSerialPeripheral

class MemFaker(wiring.Component):
    def __init__(self, name, mm, addr_width):
        self.mm = MemoryMap(addr_width=addr_width, data_width=32)
        self.mm.add_resource(name=("ram",), resource=self, size=2**addr_width)
        mm.add_window(self.mm)
        super().__init__(
            {"csr_bus": In(csr.Signature(addr_width=addr_width, data_width=32))}
        )


class Counter(wiring.Component):
    csr_bus: In(csr.Signature(addr_width=2, data_width=32))

    class Enable(csr.Register, access="rw"):
        enable: Field(action.RW, 1)

    class Counter(csr.Register, access="r"):
        value: Field(action.R, 16)

    class Overflow(csr.Register, access="rw"):
        value: Field(action.RW, 16)

    class Prescale(csr.Register, access="rw"):
        value: Field(action.RW, 16)

    def __init__(self, name="counter"):
        self.name = name
        self.enable = self.Enable()
        self.counter = self.Counter()
        self.overflow = self.Overflow()
        self._prescale = self.Prescale()

        builder = csr.Builder(name=name, addr_width=2, data_width=32)
        builder.add("enable", self.enable)
        builder.add("counter", self.counter)
        builder.add("overflow", self.overflow)
        builder.add("prescale", self._prescale)

        self._csr_bridge = csr.Bridge(builder.as_memory_map())

        super().__init__()

        self.csr_bus.memory_map = self._csr_bridge.bus.memory_map

    def elaborate(platform):
        m = Module()


class Widget(wiring.Component):
    out: Out(1)
    csr_bus: In(csr.Signature(addr_width=2, data_width=32))

    class Config(csr.Register, access="rw"):
        active: Field(action.RW, 1)
        speed: Field(action.RW, 4)
        stuff: Field(action.RW, 8)

    class Test(csr.Register, access="rw"):
        bork: Field(action.RW, 8)
        awesome: Field(action.R, 8)

    def __init__(self, name):
        self.conf = self.Config()
        self.name = name
        self.test = self.Test()

        builder = csr.Builder(name=name, addr_width=2, data_width=32)
        builder.add("config", self.conf)
        builder.add("test", self.test)

        self._csr_bridge = csr.Bridge(builder.as_memory_map())
        super().__init__()

        self.csr_bus.memory_map = self._csr_bridge.bus.memory_map


class Simple(wiring.Component):
    csr_bus: In(csr.Signature(addr_width=1, data_width=32))

    class Test(csr.Register, access="rw"):
        value: Field(action.RW, 8)
        gorf: Field(action.R, 8)

    def __init__(self, name):
        self.name = name
        self.test = self.Test()
        builder = csr.Builder(name=name, addr_width=1, data_width=32)
        builder.add("test", self.test)

        self._csr_bridge = csr.Bridge(builder.as_memory_map())
        super().__init__()

        self.csr_bus.memory_map = self._csr_bridge.bus.memory_map


class Overlord(wiring.Component):
    blink: Out(1)

    def __init__(self):
        self.memory_map = MemoryMap(addr_width=32, data_width=32)

        self.mem = MemFaker("ram", self.memory_map, 14)
        self.booter = MemFaker("bootrom",self.memory_map,12)

        self._csr_decoder = csr.Decoder(addr_width=32, data_width=32)

        self._csr_decoder.bus.memory_map = self.memory_map

        self.simple = Simple("simple")
        self.attach(self.simple)

        self.widget = Widget("widget1")
        self.attach(self.widget)

        self.widget2 = Widget("widget2")
        self.attach(self.widget2)

        self.counter = Counter()
        self.attach(self.counter)

        self.counter = Counter(name="counter2")
        self.attach(self.counter)

        self.serial = AsyncSerialPeripheral(divisor=int(16e6 // 115200), name="serial")
        self.attach(self.serial)

        super().__init__()

    def attach(self, device):
        addr = self._csr_decoder.add(device.csr_bus)

    def get(self, name):
        "get the device out"
        regs = []
        for i in self.memory_map.all_resources():
            if i.path[0] == name:
                regs.append(i)
        return regs

    def show(self):
        for i in self.memory_map.windows():
            print(i)
            sub_map = i[0]
            # print('|{}|'.format(sub_map.name))
            if sub_map.name in ["ram", "rom", "bootrom"]:
                continue
            mm = sub_map.all_resources()
            for i in mm:
                print("\t", i.path[0][0])
                res = i.resource
                wa = 0
                for j in res:
                    path = j[0][0]
                    port = j[1]
                    w = 0
                    acc = port.port.access.value.upper()
                    if not port.port.access.writable():
                        w = port.r_data.width
                    else:
                        w = port.data.width
                    print("\t\t", path, wa, wa + w - 1, acc)
                    wa = wa + w
            print()

    def new_show(self):
        for i in self.memory_map.window_patterns():
            print(i)
        print()
        for i in self.memory_map.windows():
            print(i)
            sub_map = i[0] 
            for i in sub_map.all_resources():
                print(i.path,i.start,i.end)
            mm = sub_map.all_resources()
            for i in mm:
                print("\t", i.path[0],i.start,i.end)
                name = i.path[0][0]
                res = i.resource
                wa = 0
                if name in ["ram", "rom", "bootrom"]:
                    continue
                for j in res:
                    path = j[0]
                    port = j[1]
                    w = 0
                    # acc = port.port.access.value.upper()
                    acc = port.port.access

                    rac = acc.readable()
                    wac = acc.writable()

                    width = 0
                    if rac and wac:
                        width = port.data.width
                    if rac and not wac:
                        width = port.r_data.width
                    if not rac and wac:
                        width = port.w_data.width
                    print("\t\t", path, wa, wa + w, acc)
                    wa = wa + w
            print()

if __name__ == "__main__":
    ol = Overlord()
    # r = ol.show()
    ol.new_show()
    # ol.list()
    # a = GenSVD(ol)
    # svd = open("soc.svd", "w")
    # out = a.generate_svd(file=svd)
    # # print(str(out.decode("utf-8")))
    # mem = open("memory.x","w")
    # r = GenRust(ol)
    # a = r.generate_memory_x(file=mem)
