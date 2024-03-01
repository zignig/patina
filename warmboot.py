# ice40 warmboot widget in amaranth

from amaranth import *
from amaranth.lib.wiring import *

__all__ = ["WarmBoot"]


class WarmBoot(Elaboratable):

    def __init__(self):
        self.loader = Signal()
        self.user = Signal()

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

        # state machine to run the warmboot
        with m.FSM() as fsm:
            with m.State("WAIT"):
                with m.If(self.loader | self.user):
                    m.next = "START"

            with m.State("START"):
                # meta state
                with m.If(self.loader):
                    m.next = "LOADER"
                with m.If(self.user):
                    m.next = "USER"

            with m.State("LOADER"):
                m.d.sync += image_internal.eq(0)
                m.next = "BOOT"

            with m.State("USER"):
                m.d.sync += image_internal.eq(1)
                m.next = "BOOT"

            with m.State("BOOT"):
                m.d.sync += boot_internal.eq(1)

        return m
