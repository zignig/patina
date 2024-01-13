from amaranth import *
from amaranth.utils import bits_for
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib import data, wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap
from amaranth_soc.csr import Field,action

from csr_uart import AsyncSerialPeripheral

class MemFaker(wiring.Component):
    def __init__(self, mm, addr_width):
        self.mm = MemoryMap(addr_width=addr_width, data_width=16, name="mem")
        self.mm.add_resource(name="bob",resource=(),size=2** addr_width)
        mm.add_window(self.mm)
        super().__init__(
            {"csr_bus": In(csr.Signature(addr_width=addr_width, data_width=16))}
        )

class Counter(wiring.Component):
    csr_bus: In(csr.Signature(addr_width=2, data_width=16))
    
    class Enable(csr.Register, access="rw"):
        enable: Field(action.RW,1)
    
    class Counter(csr.Register, access="r"):
        value: Field(action.R,8)
    
    class Overflow(csr.Register, access="rw"):
        value: Field(action.RW,24)
    
    def __init__(self,name="counter"):
        self.name = name 
        self.enable = self.Enable()
        self.counter = self.Counter()
        self.overflow = self.Overflow()

        self.reg_map = reg_map = csr.RegisterMap()
        reg_map.add_register(self.enable, name="enable")
        reg_map.add_register(self.counter, name="counter")
        reg_map.add_register(self.overflow, name="overflow")
        
        self._csr_bridge = csr.Bridge(reg_map, name="counter", addr_width=2, data_width=16)

        super().__init__()

        self.csr_bus.memory_map = self._csr_bridge.bus.memory_map

    def elaborate(platform):
        m = Module()
        

     
class Widget(wiring.Component):
    out: Out(1)
    csr_bus: In(csr.Signature(addr_width=2, data_width=16))

    class Config(csr.Register, access="rw"):
        active: Field(action.RW, 1)
        speed: Field(action.RW, 4)
        stuff: Field(action.RW, 8)

    class Test(csr.Register, access="rw"):
        bork: Field(action.RW, 8)
        awesome: Field(action.RW, 8)

    def __init__(self, name):
        self.conf = self.Config()
        self.name = name
        self.test = self.Test()

        self.reg_map = reg_map = csr.RegisterMap()
        reg_map.add_register(self.conf, name="config")
        reg_map.add_register(self.test, name="test")


        self._csr_bridge = csr.Bridge(reg_map, name=name, addr_width=2, data_width=16)

        super().__init__()

        self.csr_bus.memory_map = self._csr_bridge.bus.memory_map


class Overlord(wiring.Component):
    blink: Out(1)

    def __init__(self):
        self._devices = {}
        self.mem_map = MemoryMap(addr_width=16, data_width=16)

        self.mem = MemFaker(self.mem_map,13)

        self._csr_decoder = csr.Decoder(addr_width=16, data_width=16)

        self._csr_decoder.bus.memory_map = self.mem_map
        
        self.widget = Widget("first")
        self.attach(self.widget)

        self.widget2 = Widget("second")
        self.attach(self.widget2)
        # self._csr_decoder.add(self.widget2.csr_bus)

        self.counter=  Counter()
        self.attach(self.counter)
        
        self.uart = AsyncSerialPeripheral(name='uart0',divisor=4000)
        self.attach(self.uart)

        # self.uart1 = AsyncSerialPeripheral(name='uart1',divisor=4000)
        # self.attach(self.uart1)

        super().__init__()
        
    def attach(self,device):
        addr = self._csr_decoder.add(device.csr_bus)
        self._devices[device.name] = (device,addr)

    def get(self,name):
        "get the device out "
        regs = []
        for i in self.mem_map.all_resources():
            if i.path[0] == name:
                regs.append(i)
        return regs 
    
    def show(self):
        mm = self.mem_map.all_resources()
        for i in mm:
            print(i.path,i.start,i.end,i.resource)
        full = []
        for i,j in self._devices.items():
            map = self.get(i)
            map2 = list(j[0].reg_map.flatten())
            print(i)
            #print(map)
            #print(map2)
            r = zip(map,map2)
            print(list(r))
            full.append(list(r))
        for i in self.mem_map.window_patterns():
             print(i)
        return full

    def list(self):
        for i,j in self._devices.items():
            #print(i,j)
            print(i)
            periph = j[0]
            for k in periph.reg_map.flatten():
                reg = k[0]
                print(k,reg.element.width)
                for l in reg.f.flatten():
                    el = l[1]
                    print(l[0],el.port.shape.width,el.port.access)
                    
                    #print(dir(el),el)

if __name__ == "__main__":
    ol = Overlord()
    #r = ol.show()
    ol.list()
