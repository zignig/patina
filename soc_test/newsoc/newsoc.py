from amaranth import *
from amaranth.back import rtlil
from amaranth.build import ResourceError, Resource, Pins, Attrs
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr, wishbone
from amaranth_soc.csr.wishbone import WishboneCSRBridge

from minerva.core import Minerva
from memory import WishboneMemory
from csr_uart import AsyncSerialPeripheral


from amaranth_boards.resources.interface import UARTResource
from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform

__all__ = ["SimpleSoC"]


class SimpleSoC(Elaboratable):
    def __init__(self, *, rom_init=()):
        self._cpu = Minerva(with_icache=True, icache_base=0x0, icache_limit=0x1000)
        self._ram = WishboneMemory(
            size=8192,
            data_width=32,
            granularity=8,
            name="ram",
        )
        self._rom = WishboneMemory(
            size=512,
            writable=False,
            data_width=32,
            granularity=8,
            name="rom",
            init=rom_init,
        )
        self._serial = AsyncSerialPeripheral(divisor=int(1e6 // 115200), name="serial")

        self._csr_dec = csr.Decoder(addr_width=31, data_width=8)
        self._csr_dec.add(self._serial.csr_bus)

        self._wb_csr = WishboneCSRBridge(self._csr_dec.bus, data_width=32)
        self._wb_dec = wishbone.Decoder(
            addr_width=30, data_width=32, granularity=8, features={"cti", "bte"}
        )
        self._wb_arb = wishbone.Arbiter(
            addr_width=30, data_width=32, granularity=8, features={"cti", "bte"}
        )

        self._cpu_ibus = wishbone.Interface(
            addr_width=30, data_width=32, granularity=8, features={"err", "cti", "bte"}
        )
        self._cpu_dbus = wishbone.Interface(
            addr_width=30, data_width=32, granularity=8, features={"err", "cti", "bte"}
        )
        self._wb_arb.add(self._cpu_ibus)
        self._wb_arb.add(self._cpu_dbus)

        self._wb_dec.add(self._rom.bus)
        self._wb_dec.add(self._ram.bus)
        self._wb_dec.add(flipped(self._wb_csr.wb_bus), addr=0x8000)

    def elaborate(self, platform):
        m = Module()

        m.submodules.cpu = self._cpu
        m.submodules.rom = self._rom
        m.submodules.serial = self._serial
        m.submodules.wb_arb = self._wb_arb
        m.submodules.wb_dec = self._wb_dec
        m.submodules.wb_csr = self._wb_csr
        m.submodules.csr_dec = self._csr_dec

        connect(m, self._wb_arb.bus, self._wb_dec.bus),

        m.d.comb += [
            self._cpu_ibus.cyc.eq(self._cpu.ibus.cyc),
            self._cpu_ibus.stb.eq(self._cpu.ibus.stb),
            self._cpu_ibus.adr.eq(self._cpu.ibus.adr),
            self._cpu_ibus.sel.eq(self._cpu.ibus.sel),
            self._cpu_ibus.cti.eq(self._cpu.ibus.cti),
            self._cpu_ibus.bte.eq(self._cpu.ibus.bte),
            self._cpu.ibus.ack.eq(self._cpu_ibus.ack),
            self._cpu.ibus.err.eq(self._cpu_ibus.err),
            self._cpu.ibus.dat_r.eq(self._cpu_ibus.dat_r),
            self._cpu_dbus.cyc.eq(self._cpu.dbus.cyc),
            self._cpu_dbus.stb.eq(self._cpu.dbus.stb),
            self._cpu_dbus.adr.eq(self._cpu.dbus.adr),
            self._cpu_dbus.sel.eq(self._cpu.dbus.sel),
            self._cpu_dbus.we.eq(self._cpu.dbus.we),
            self._cpu_dbus.dat_w.eq(self._cpu.dbus.dat_w),
            self._cpu_dbus.cti.eq(self._cpu.dbus.cti),
            self._cpu_dbus.bte.eq(self._cpu.dbus.bte),
            self._cpu.dbus.ack.eq(self._cpu_dbus.ack),
            self._cpu.dbus.err.eq(self._cpu_dbus.err),
            self._cpu.dbus.dat_r.eq(self._cpu_dbus.dat_r),
        ]
        uartpins = platform.request("uart", 0)

        m.d.comb += [
            uartpins.tx.o.eq(self._serial._phy.tx.o),
            self._serial._phy.rx.i.eq(uartpins.rx.i),
        ]
        return m


p = TinyFPGABXPlatform()
# 3.3V FTDI connected to the tinybx.
# pico running micro python to run
p.add_resources(
    [
        UARTResource(
            0, rx="A8", tx="B8", attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1)
        ),
        Resource("reset_pin", 0, Pins("A9", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("warmboot", 0, Pins("H2", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
    ]
)
a = SimpleSoC()
p.build(a)  # ,do_program=True)
