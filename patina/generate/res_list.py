# Resource extraction testing

import amaranth_soc
from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap, ResourceInfo


class ResList:
    def __init__(self, soc):
        self._soc = soc
        self.mm: MemoryMap = self._soc.fabric.memory_map

    def show_win(self, window, depth=0):
        for w, name, (start, stop, ratio) in window.windows():
            print(depth * "   ", name, start, stop)
            if len(list(w._windows)) > 0:
                depth += 1
                for sw in w.windows():
                    print(sw.resource)
                    #self.show_win(sw, depth=depth)
            # for i in w.all_resources():
            #     print(i.resource)

    def generate(self):
        self.show_win(self.mm)
        return
        for r, res in self.mm._ranges.items():
            print(r, res)
        print("-----")
        for w, name, (start, stop, ratio) in self.mm.windows():
            print(name, start, stop)

        for window, name, (start, stop, ratio) in self.mm.windows():
            # if not hasattr(window,"csr_only"):
            # continue
            print(name)
            print("->", window._windows)
            for i in window.all_resources():
                if isinstance(i.resource, csr.Register):
                    # print("tag",i.path)
                    reg = i.resource
                    for f in reg:
                        print("\t", f)
