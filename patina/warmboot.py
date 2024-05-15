# ice40 warmboot widget in amaranth

from amaranth import *
from amaranth.lib.wiring import *

__all__ = ["WarmBoot"]

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

class WarmBoot(Component):

    bus: In(BusPort(addr=1, data=16))

    def __init__(self):
        super().__init__()
        self.internal = Signal()
        self.external = Signal()

    def elaborate(self, platform):
        m = Module()
        # Warm boot object
        image_internal = Signal(2, init=1)
        boot_internal = Signal()

        m.submodules.wb = Instance(
            "SB_WARMBOOT",
            i_S1=image_internal[1],
            i_S0=image_internal[0],
            i_BOOT=boot_internal,
        )

        # bus cmd shorthand
        cmd = self.bus.cmd

        with m.If(cmd.valid & (cmd.payload.lanes == 3 )):
            m.d.sync += self.internal.eq(1)

        # state machine to run the warmboot
        with m.FSM() as fsm:
            with m.State("INIT"):
                with m.If(self.internal == 1):
                    m.next = "START"
                with m.If(self.external):
                    m.next = "USER"

            with m.State("START"):
                m.d.sync += image_internal.eq(0)
                m.next = "BOOT"

            with m.State("USER"):
                m.d.sync += image_internal.eq(1)
                m.next = "BOOT"

            with m.State("BOOT"):
                m.d.sync += boot_internal.eq(1)
        return m
