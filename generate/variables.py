# generate a lib.rs file for system variables
from hapenny.mem import BasicMemory, SpramMemory


class RustLib:
    def __init__(self, soc):
        self._soc = soc

    def gen_lib_rs(self, file=None):

        def emit(content):
            """Utility function that emits a string to the targeted file."""
            print(content, file=file)

        for i in self._soc.memory_map.all_resources():
            res = i.resource
            name = i.resource.name
            start = i.start
            sec_length = i.end - i.start
            # exclude the storage memory
            if isinstance(res, (BasicMemory, SpramMemory)):
                continue
            emit(
                "    pub const {name}: u32 = 0x{addr:01X} ; // {addr}".format(
                    name=name.upper()+"_ADDR", addr=i.start
                )
            )
            # log(res,name,start,sec_length)
