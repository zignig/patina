# a SPI master for Hapenny

from amaranth import *
from amaranth.lib.cdc import FFSynchronizer
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib.wiring import *
from amaranth.lib.enum import *
from amaranth.lib.coding import Encoder, Decoder

from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

# taken from
# https://github.com/tpwrules/ice_panel/commit/147969bdeedb5d4990045fcd4976b2f95704ad4c
# converted to hapenny bus

# Register Map

# 0x0: (W) Transaction Start / (R) Status
#   Write: writing starts a transaction. it is only legal to start a transaction
#          when one is not already in progress.
#          bit 15: 1 for write transaction, 0 for read transaction
#           14-13: bus mode: 0 = previous, 1 = 1 bit, 2 = 2 bit, 3 = 4 bit
#              12: 1 if chip select should be deasserted at txn end
#            11-0: transaction length
#    Read: bit 15: 1 if transaction in progress, 0 otherwise. the transaction
#                  FIFO is empty/full and the bus is idle iff this bit is 0
#           14:13: current bus mode

# 0x1: (W) Queue Write / (R) Receive Read/FIFO status
# Write:      7-0: character to write on bus. only legal if in write mode.
#  Read:   bit 15: bit 0 of read character, if RX FIFO is not empty in read mode
#          bit 14: 1 if RX fifo is empty, 0 otherwise (in read mode)
#                  1 if TX fifo is full, 0 otherwise (in write mode)
#             6-0: remaining bits of char, if RX fifo is not empty in read mode


class SetReset(Elaboratable):
    def __init__(self, parent, *, priority, initial=False):
        # if both set and reset are asserted on the same cycle, the value
        # becomes the prioritized state.
        if priority not in ("set", "reset"):
            raise ValueError(
                "Priority must be either 'set' or 'reset', "
                "not '{}'.".format(priority)
            )

        self.priority = priority

        self.set = Signal()
        self.reset = Signal()
        self.value = Signal(reset=initial)

        # avoid the user having to remember to add us
        parent.submodules += self

    def elaborate(self, platform):
        m = Module()

        if self.priority == "set":
            with m.If(self.set):
                m.d.sync += self.value.eq(1)
            with m.Elif(self.reset):
                m.d.sync += self.value.eq(0)
        elif self.priority == "reset":
            with m.If(self.reset):
                m.d.sync += self.value.eq(0)
            with m.Elif(self.set):
                m.d.sync += self.value.eq(1)

        return m


class SimpleSPI(Component):
    """
    SimpleSPI provides a nifty spi interface in gateware


    """
    # hapenny bus
    bus: In(BusPort(addr=1, data=16))
    # Spi
    clk: Out(1)
    cs: Out(1)
    copi: Out(1)
    cipo: In(1)

    def __init__(self,start_addr=0,flash_size=0, fifo_depth=16):
        super().__init__()
        self.start_addr = start_addr
        self.flash_size = flash_size
        self.fifo = SyncFIFOBuffered(width=8, depth=fifo_depth)

    # the builder will ask for extra data for the infomap when it
    # builds the fabric 

    def extra(self):
        return {"start_addr":self.start_addr,"flash_size":self.flash_size}
    
    def elaborate(self, platform):
        m = Module()
        m.submodules.fifo = fifo = self.fifo

        # define the signals that make up the registers
        r0_txn_active = SetReset(m, priority="set")
        r0_write_txn = Signal()
        r0_bus_mode = Signal(2, reset=1)
        r0_deassert_cs = Signal()
        r0_txn_length = Signal(12)

        # register the bus response
        read_data = Signal(16)  # it expects one cycle of read latency
        m.d.sync += self.bus.resp.eq(read_data)

        # bus cmd shorthand
        cmd = self.bus.cmd
        
        # read
        with m.If(cmd.valid & (cmd.payload.lanes == 0)):
            with m.Switch(cmd.payload.addr):
                with m.Case(0):  # status register
                    m.d.comb += [
                        read_data[15].eq(r0_txn_active.value),
                        read_data[13:15].eq(r0_bus_mode),
                    ]
                with m.Case(1):  # receive read/FIFO status register
                    with m.If(r0_write_txn):
                        # interested in if the write side of the fifo is full
                        m.d.comb += read_data[14].eq(~fifo.w_rdy)
                    with m.Else():
                        # interested in if the read side of the fifo is empty
                        m.d.comb += read_data[14].eq(~fifo.r_rdy)
                        with m.If(fifo.r_rdy):
                            m.d.comb += [
                                fifo.r_en.eq(1),  # if it is, acknowledge it
                                # and give the user the current byte
                                read_data[15].eq(fifo.r_data[0]),
                                read_data[:7].eq(fifo.r_data[1:]),
                            ]
        # write
        with m.Elif(cmd.valid & (cmd.payload.lanes.any())):
            with m.Switch(cmd.payload.addr):
                with m.Case(0):  # transaction start register
                    with m.If(~r0_txn_active.value):
                        with m.If(cmd.payload.data[:12] != 0):
                            m.d.comb += r0_txn_active.set.eq(1)
                        m.d.sync += [
                            r0_write_txn.eq(cmd.payload.data[15]),
                            r0_bus_mode.eq(
                                Mux(
                                    cmd.payload.data[13:15] == 0,
                                    r0_bus_mode,
                                    cmd.payload.data[13:15],
                                )
                            ),
                            r0_deassert_cs.eq(cmd.payload.data[12]),
                            r0_txn_length.eq(cmd.payload.data[:12]),
                        ]
                with m.Case(1):  # tx queue register
                    with m.If(r0_write_txn & fifo.w_rdy):
                        m.d.comb += [
                            fifo.w_data.eq(cmd.payload.data[:8]),
                            fifo.w_en.eq(1),
                        ]

        # this is a crappy state machine but at this point i just want something
        # that does actually work

        bit_ctr = Signal(range(7))
        curr_buf = Signal(8)

        with m.FSM("STOP"):
            with m.State("STOP"):  # no transaction happening
                with m.If(r0_txn_active.value):
                    # automatically assert CS at start of transaction
                    m.d.sync += self.cs.eq(0)
                    with m.If(r0_write_txn):
                        m.next = "WIDLE"
                    with m.Else():
                        m.next = "RIDLE"
                with m.Elif(r0_deassert_cs):
                    # deassert CS once transaction stops if asked
                    m.d.sync += self.cs.eq(1)

            with m.State("WIDLE"):  # write transaction, waiting for data
                with m.If(fifo.r_rdy):  # have we got some?
                    # yes, acknowledge it
                    m.d.comb += fifo.r_en.eq(1)
                    m.d.sync += [  # and prepare to write the byte
                        curr_buf.eq(fifo.r_data),
                        bit_ctr.eq(7),
                        r0_txn_length.eq(r0_txn_length - 1),
                    ]
                    m.next = "WOUTA"

            with m.State("WOUTA"):
                # the flash latches in the new value on the rising edge.
                # so output the current data bit along with a low clock
                m.d.comb += [
                    self.copi.eq(curr_buf[-1]),
                    self.clk.eq(0),
                ]
                m.next = "WOUTB"

            with m.State("WOUTB"):
                # now that the value is output, we can raise the clock and the
                # flash will latch it in.
                m.d.comb += [
                    self.copi.eq(curr_buf[-1]),
                    self.clk.eq(1),
                ]
                with m.If(bit_ctr == 0):
                    with m.If(r0_txn_length == 0):
                        m.d.comb += r0_txn_active.reset.eq(1)
                        m.next = "STOP"
                    with m.Else():
                        m.next = "WIDLE"
                with m.Else():
                    m.d.sync += bit_ctr.eq(bit_ctr - 1)
                    m.d.sync += curr_buf.eq(curr_buf << 1)
                    m.next = "WOUTA"

            with m.State("RIDLE"):  # read transaction, waiting for space
                with m.If(fifo.w_rdy):  # have we got some?
                    # yes, start reading a byte from the flash
                    m.d.sync += bit_ctr.eq(7)
                    m.d.sync += r0_txn_length.eq(r0_txn_length - 1)
                    m.next = "RINA"

            with m.State("RINA"):
                # the device clocks out data on the falling edge. since the edge
                # fell when the last read or write ended, start by latching in
                # the current bit.
                m.d.sync += curr_buf.eq(Cat(self.cipo, curr_buf[:-1]))
                m.d.comb += self.clk.eq(0)
                m.next = "RINB"

            with m.State("RINB"):
                m.d.comb += self.clk.eq(1)
                with m.If(bit_ctr == 0):
                    m.d.comb += [
                        fifo.w_data.eq(curr_buf),
                        fifo.w_en.eq(1),
                    ]
                    with m.If(r0_txn_length == 0):
                        m.d.comb += r0_txn_active.reset.eq(1)
                        m.next = "STOP"
                    with m.Else():
                        m.next = "RIDLE"
                with m.Else():
                    m.d.sync += bit_ctr.eq(bit_ctr - 1)
                    m.next = "RINA"

        return m
