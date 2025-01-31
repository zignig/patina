# Resource extraction testing

import amaranth_soc
from amaranth_soc import csr
from amaranth_soc.memory import MemoryMap, ResourceInfo


class ResList:
    def __init__(self,soc):
        self._soc = soc
        self.mm = self._soc.fabric.memory_map

    def generate(self):
        # for i in self.mm.all_resources():
        #     print(i.path,i.start,i.end,i.resource)
        #     print()
        #     if isinstance(i.resource,csr.Register):
        #         reg = i.resource
        #         for f in reg:
        #             print("\t",f)
        #             # print(dir(f))
        #         print("--")
        # print("-----")
        # return
        for window , name , (start,stop,ratio) in self.mm.windows():
            if not hasattr(window,"csr_only"):
                continue
            print(window)
            for i in window.all_resources():
                print(i.path,i.start+start,i.end+stop)
                if isinstance(i.resource,csr.Register):
                    # print("tag",i.path)
                    reg = i.resource
                    for f in reg:
                        print("\t",f)

                         

        
                    