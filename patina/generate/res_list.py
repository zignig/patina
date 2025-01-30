# Resource extraction testing

import amaranth_soc
from amaranth_soc.memory import MemoryMap, ResourceInfo


class ResList:
    def __init__(self,soc):
        self._soc = soc
        self.mm = self._soc.fabric.memory_map

    def generate(self):
        for window , name , (start,stop,ratio) in self.mm.windows():
            print(window,start,stop)
            if not hasattr(window,"csr_only"):
                    continue
            for w2 in window.all_resources():
                print("  ",w2.path,w2,start,w2.end)
                res = w2.resource
                print(res.bus.memory_map)
                # print(dir(res))
                