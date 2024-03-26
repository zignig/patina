from functools import reduce

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.lib.enum import *
from amaranth.lib.coding import Encoder, Decoder

from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, treeduce
from hapenny.bus import SimpleFabric, partial_decode, BusPort
from hapenny.mem import BasicMemory

import logging

log = logging.getLogger(__name__)


class BootMem(BasicMemory):
    """A subclass of the Basic mem for the bootloader"""

    def __init__(self, boot_image, image_size=None):
        if image_size == None:
            image_size = 2 ** (len(boot_image)).bit_length()
        else:
            image_size = image_size
        super().__init__(depth=image_size, read_only=True, contents=boot_image)


class FabricBuilder(Component):
    # Takes a list of devices builds a memory map
    # and calculates bit width for a SimpleFabric Build
    def __init__(
        self,
        devices,
        name="fabric",
    ):
        self.devices = devices

        def div():
            log.info("-" * 20)
            log.info("")

        log.info("")
        log.info("Device Scan")
        div()

        # generate unique name for memory bus
        name_dict = {}

        def uniq_name(name):
            if name in name_dict:
                name_dict[name] += 1
                return name + "_" + str(name_dict[name])
            else:
                name_dict[name] = 0
                return name

        # add attrs to the python objects
        for d in devices:
            d.name = uniq_name(d.__class__.__qualname__)
            d.width = d.bus.cmd.payload.addr.shape().width
            log.info(f"{d.name} - {d.width}")

        self.addr_width = addr_width = max(d.width for d in devices)
        self.extra_bits = extra_bits = (len(devices) - 1).bit_length()

        log.info("bus width %d (hw)", self.addr_width)
        log.info("bus extra bits %d (hw)", self.extra_bits)
        log.info(f"total width {addr_width+extra_bits} (hw)")
        div()

        # Create the memory map for the fabric itself
        self.memory_map = memory_map = MemoryMap(
            addr_width=addr_width + extra_bits + 1,
            data_width=16,
            name=name,
            alignment=addr_width,
        )

        # build the memory map list
        for d in devices:
            log.critical(d.name)
            device_memory = MemoryMap(
                addr_width=d.width + 1, data_width=16, name=d.name
            )
            device_memory.add_resource(d, name=(d.name,), size=2 ** (d.width + 1))
            memory_map.add_window(device_memory)

        # show the memory map
        log.critical("")
        div()
        for i in self.memory_map.window_patterns():
            log.critical(f"{i[0]} \t  {i[1][0]}, {len(i[1][0])}")
        # show the resources
        div()
        for i in self.memory_map.all_resources():
            log.critical(f"{i.path[0]} \t{i.start} \t{i.end}")

        self.bus = BusPort(addr=addr_width - 1, data=16).flip().create()

    def elaborate(self, platform):
        log.warning("Elaborate Bus")
        m = Module()

        return m
