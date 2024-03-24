# twiddler

from amaranth import *
from amaranth.lib.wiring import *


class Twiddle(Elaboratable):
    def __init__(self):
        self.outpin = Signal()

    def elaborate(self, platform):

        m = Module()
        #pin = platform.request("boot",0)
        enable_pin = platform.request("user",0)
        enable = Signal()
        #print(dir(pin))
        #print(pin,enable,enable_pin)

        #m.d.comb += enable.eq(pin.i)

        half_freq = int(platform.default_clk_frequency // 2)
        timer = Signal(range(half_freq + 1))
        #with m.If(enable):
        with m.If(timer == half_freq):
            m.d.sync += enable_pin.o.eq(~enable_pin.o)
            m.d.sync += timer.eq(0)
        with m.Else():
            m.d.sync += timer.eq(timer + 1)
        return m

