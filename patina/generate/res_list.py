# Resource extraction testing

import amaranth_soc
from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap, ResourceInfo


class ResList:
    def __init__(self, soc):
        self._soc = soc
        self.mm: MemoryMap = self._soc.fabric.memory_map

    def res(self):
        max_length = 0 
        for i in self.mm.all_resources():
            path = ' / '.join(list( map(lambda x:x[0].upper(),list(i.path))))
            if len(path) > max_length: 
                max_length = len(path)
        for i in self.mm.all_resources():
            path = ' / '.join(list( map(lambda x:x[0].upper(),list(i.path))))
            print(path.ljust(max_length),' | ',str(i.start).ljust(8),str(i.end).ljust(8))

    def rec(self,window,depth=0):
        for win, name, (pattern,ratio) in window.window_patterns():
            # print(dir(window))
            path = ' / '.join(list( map(lambda x:x[0].upper(),list(name))))
            print(path.ljust(20),' | ',pattern)
            if len(win._windows) > 0:
                depth += 1 

                self.rec(win,depth=depth)
        
    def find_csr_window(self):
        for window, name, (start, end, _) in self.mm.windows():
            if not hasattr(window, "csr_only"):
                continue
            print(name, start, end)
            return (window, start, end)
        raise(Exception("no csr window"))

    def generate(self):
        # display stuff
        self.res()
        print()
        self.rec(self.mm)
        # self.rec(self.mm)
        # print()
        # # find the csr window
        (window, start, end) = self.find_csr_window()
        print(start)
        self.peripheral(window)

    def peripheral(self, window):
        for window, name, (start, end, _) in window.windows():
            print(name, start, end)
            for register in window.all_resources():
                self.register(register, start + register.start)

    def register(self, register, offset):
        print("\t", register.path, offset)
        pos = 0
        for name, field in register.resource:
            # print('\t\t',dir(field))
            width = field.port.shape.width
            print("\t\t", name, pos, pos + width)
            pos = pos + width
