# This is a watch dog.
# If it is not fed , it will reboot the SOC
# mainly so I don't have to go back uout to the
# workshop to press the reset button (again)

from amaranth import *
from amaranth.lib.wiring import *

__all__ = ["Watchdog"]

from hapenny import StreamSig, AlwaysReady, mux, oneof, lohalf, hihalf
from hapenny.bus import BusPort


class Watchdog(Component):
    "Count down to zero , and hard fail."
    bus: In(BusPort(addr=1, data=16))
    activate: Out(1)

    def __init__(self, active=True):
        "Just run for now, for testing"
        self.max = int(500e6)
        self.boop = Signal()
        self.counter = Signal(32, init=int(self.max))
        self.running = Signal()
        super().__init__()

    def elaborate(self, platform):
        m = Module()
        #
        # increment the counter
        # bus cmd shorthand
        cmd = self.bus.cmd

        with m.If(cmd.valid):
            with m.If(cmd.payload.lanes.any()):
                m.d.sync += [self.counter.eq(self.max), self.running.eq(True)]
            with m.If(cmd.payload.lanes == 0):
                with m.Switch(cmd.payload.addr):
                    with m.Case(1):
                        m.d.sync += self.bus.resp.eq(hihalf(self.counter))
        with m.Elif(self.running):
            m.d.sync += [self.counter.eq(self.counter - 1)]

        # activate
        with m.If(self.counter == 0):
            m.d.sync += self.activate.eq(1)

        # ok do nothing for now
        return m
