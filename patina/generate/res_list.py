# Resource extraction testing

import amaranth_soc
from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap, ResourceInfo


class ResList:
    def __init__(self, soc):
        self._soc = soc
        self.mm: MemoryMap = self._soc.fabric.memory_map


    def find_csr_window(self):
        for window ,name,(start,end,_) in self.mm.windows():
            if not hasattr(window,"csr_only"):
                continue
            print(name,start,end)
            return (window,start,end)

    def generate(self):
        # find the csr window
        ( window , start, end)  = self.find_csr_window()
        print(start,end)
        # for w in window.windows():
            # print(w[1])
        for register in window.all_resources():
            # print('\t',register.path)
            # print(register.start)
            print(register.path,register.start)
            for i in register.resource.f.flatten():
                print(i)
                # for j in i:
                #     print(j)

            print()