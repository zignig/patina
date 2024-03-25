from functools import reduce

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.lib.enum import *
from amaranth.lib.coding import Encoder, Decoder

from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, treeduce

import logging

log = logging.getLogger(__name__)


class BusCmd(Signature):
    def __init__(self, *, addr, data):
        if isinstance(data, int):
            lanes = (data + 7) // 8
        else:
            lanes = (data.width + 7) // 8
        super().__init__({"addr": Out(addr), "lanes": Out(lanes), "data": Out(data)})


class BusPort(Signature):
    def __init__(self, *, addr, data):
        super().__init__(
            {
                "cmd": Out(AlwaysReady(BusCmd(addr=addr, data=data))),
                "resp": In(data),
            }
        )


def partial_decode(m, bus, width):
    assert (
        width >= bus.cmd.payload.addr.shape().width
    ), "can't use partial_decode to make a bus narrower"
    log.warning(f"device size {bus.cmd.payload.addr.shape().width} to {width}")
    port = BusPort(addr=width, data=bus.cmd.payload.data.shape()).flip().create()
    m.d.comb += [
        bus.cmd.payload.addr.eq(port.cmd.payload.addr),
        bus.cmd.payload.data.eq(port.cmd.payload.data),
        bus.cmd.payload.lanes.eq(port.cmd.payload.lanes),
        bus.cmd.valid.eq(port.cmd.valid),
        port.resp.eq(bus.resp),
    ]
    return port


def narrow_addr(m, bus, width):
    assert (
        width <= bus.cmd.payload.addr.shape().width
    ), "can't use narrow_addr to make a bus wider"
    port = BusPort(addr=width, data=bus.cmd.payload.data.shape()).flip().create()
    m.d.comb += [
        bus.cmd.payload.addr.eq(port.cmd.payload.addr),
        bus.cmd.payload.data.eq(port.cmd.payload.data),
        bus.cmd.payload.lanes.eq(port.cmd.payload.lanes),
        bus.cmd.valid.eq(port.cmd.valid),
        port.resp.eq(bus.resp),
    ]
    return port


class SimpleFabric(Elaboratable):
    def __init__(self, devices):
        assert len(devices) > 0

        data_bits = max(p.cmd.payload.data.shape().width for p in devices)
        addr_bits = max(p.cmd.payload.addr.shape().width for p in devices)

        sig = BusPort(addr=addr_bits, data=data_bits).flip()
        log.info(f"fabric configured for {addr_bits} addr bits, {data_bits} data bits")
        # for i, d in enumerate(devices):
        #     assert sig.is_compliant(d), \
        #             f"device #{i} does not have {addr_bits} addr bits: {d.cmd.payload.addr.shape()}"
        self.devices = devices
        self.extra_bits = (len(devices) - 1).bit_length()
        self.addr_bits = addr_bits
        self.data_bits = data_bits
        log.warning(f"addr {addr_bits} extra {self.extra_bits}")
        self.bus = (
            BusPort(addr=addr_bits + self.extra_bits, data=data_bits).flip().create()
        )

    def elaborate(self, platform):
        m = Module()

        # index of the currently selected device.
        devid = Signal(self.extra_bits)
        m.d.comb += devid.eq(self.bus.cmd.payload.addr[self.addr_bits :])

        # index of the last selected device (registered).
        last_id = Signal(self.extra_bits)
        # Since the setting of the response mux is ignored if the CPU isn't
        # expecting data back, we can just capture the address lines on every
        # cycle whether it's valid or not.
        m.d.sync += last_id.eq(devid)

        for i, d in enumerate(self.devices):
            # Fan out the incoming address, data, and lanes to every device.
            m.d.comb += [
                d.cmd.payload.addr.eq(self.bus.cmd.payload.addr),
                d.cmd.payload.data.eq(self.bus.cmd.payload.data),
                d.cmd.payload.lanes.eq(self.bus.cmd.payload.lanes),
            ]
            # Only propagate cmd valid to the specific addressed device.
            dv = Signal(1, name=f"valid_{i}")
            m.d.comb += [
                dv.eq(self.bus.cmd.valid & (devid == i)),
                d.cmd.valid.eq(dv),
            ]

        # Fan the response data in based on who we're listening to.
        response_data = []
        for i, d in enumerate(self.devices):
            data = d.resp & (last_id == i).replicate(self.data_bits)
            response_data.append(data)

        m.d.comb += self.bus.resp.eq(treeduce(lambda a, b: a | b, response_data))

        return m


class SMCFabric(Component):
    # Slightly More Complicated Fabric
    def __init__(
        self,
        devices,
        addr_width=None,
        name="fabric",
    ):
        log.info("")
        log.info("Device Scan")
        for d in devices:
            log.info(f"{d.name} - {d.bus.cmd.payload.addr.shape()}")
        log.info("-" * 20)
        # Create the memory map for the fabric
        # find the max width

        self.name = name

        # if addr_width == 32:
        addr_width = max(p.memory_map.addr_width for p in devices) - 1
        #addr_width = 12
        
        self.addr_width = addr_width
        self.extra_bits = extra_bits = (len(devices) - 1).bit_length()

        log.info("bus width %d", self.addr_width)
        log.info("bus extra bits %d", self.extra_bits)
        log.info(f"total width {addr_width+extra_bits}")

        self.memory_map = MemoryMap(
            addr_width=addr_width + extra_bits,
            data_width=16,
            name=name,
            alignment=addr_width,
        )

        self.devices = {}
        for device in devices:
            log.debug("\t {} - {}".format(device.name, device.memory_map.addr_width))
            self.devices[device.memory_map] = device
            self.memory_map.add_window(device.memory_map)

        self.bus = BusPort(addr=addr_width - 1, data=16).flip().create()

    def find(self, item):
        pass

    def elaborate(self, platform):
        log.warning("Elaborate Bus")
        m = Module()
        # attach  the devices
        for d in self.devices.values():
            log.warning("attach %s", d.name)
            m.submodules[d.name] = d

        for sub_map, (sub_pat, sub_ratio) in self.memory_map.window_patterns():
            print(self.devices[sub_map], sub_map)

        device_buses = []
        for db in self.devices.values():
            # log.error(db)
            device_buses.append(db.bus)
        # index of the currently selected device.
        # log.error(device_buses)
        devid = Signal(self.extra_bits)
        m.d.comb += devid.eq(self.bus.cmd.payload.addr[self.addr_width :])

        # index of the last selected device (registered).

        last_id = Signal(self.extra_bits)
        # Since the setting of the response mux is ignored if the CPU isn't
        # expecting data back, we can just capture the address lines on every
        # cycle whether it's valid or not.
        m.d.sync += last_id.eq(devid)

        for i, d in enumerate(device_buses):
            log.error("%d , %s", i, d)
            # Fan out the incoming address, data, and lanes to every device.
            m.d.comb += [
                d.cmd.payload.addr.eq(self.bus.cmd.payload.addr),
                d.cmd.payload.data.eq(self.bus.cmd.payload.data),
                d.cmd.payload.lanes.eq(self.bus.cmd.payload.lanes),
            ]
            # Only propagate cmd valid to the specific addressed device.
            dv = Signal(1, name=f"valid_{i}")
            m.d.comb += [
                dv.eq(self.bus.cmd.valid & (devid == i)),
                d.cmd.valid.eq(dv),
            ]

        # Fan the response data in based on who we're listening to.
        response_data = []
        for i, d in enumerate(device_buses):
            data = d.resp & (last_id == i).replicate(16)
            response_data.append(data)
        m.d.comb += self.bus.resp.eq(treeduce(lambda a, b: a | b, response_data))

        # fan_in = 0
        # with m.Switch(self.bus.cmd.payload.addr):
        #     for sub_map, (sub_pat, sub_ratio) in self.memory_map.window_patterns():
        #         print(self.devices[sub_map])
        #         sub_bus = self.devices[sub_map].memory_map
        #         sub = self.devices[sub_map].bus
        #         sub_name = self.devices[sub_map].name
        #         # Bind the outgoing data and lanes
        #         m.d.comb += [
        #             sub.cmd.payload.addr.eq(
        #                 self.bus.cmd.payload.addr[:sub_bus.addr_width]
        #             ),
        #             sub.cmd.payload.data.eq(self.bus.cmd.payload.data),
        #             sub.cmd.payload.lanes.eq(self.bus.cmd.payload.lanes),
        #         ]
        #         print(sub_pat)
        #         with m.Case(sub_pat):
        #             m.d.comb += sub.cmd.valid.eq(self.bus.cmd.valid)
        #             m.d.comb += self.bus.resp.eq(sub.resp)
        #             #m.d.comb += self.bus.resp.eq(12)

        #         fan_in |= sub.resp
        # raise("bork on mem bus")
        # convert this to full address range
        # Fan the response data in based on who we're listening to.
        # response_data = []
        # for i, d in enumerate(self.devices):
        #     data = d.resp & (last_id == i).replicate(self.data_bits)
        #     response_data.append(data)

        # m.d.comb += self.bus.resp.eq(treeduce(lambda a, b: a | b, response_data))
        # m.d.comb += self.bus.resp.eq(fan_in)

        return m
