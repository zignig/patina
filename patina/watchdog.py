# This is a watch dog.
# If it is not fed , it will reboot the SOC
# mainly so I don't have to go back uout to the 
# workshop to press the reset button (again)

from amaranth import *
from amaranth.lib.wiring import *

__all__ = ["Watchdog"]

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

class Watchdog(Component):
    "Count down to zero , and hard fail. "
    bus: In(BusPort(addr=1, data=16))

    def __init__(self,active=True):
        " Just run for now, for testing"
        self.boop = Signal()
        self.active = Signal(active)
        self.counter = Signal(32)
        super().__init__()

    def elaborate(self, platform):
        m = Module()
        # 
        # increment the counter
        m.d.sync  += [
            self.counter.eq(self.counter + 1)
        ]
        # ok do nothing for now
        return m
