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
        # generate unique name for memory bus
        name_dict = {}

        def div():
            log.debug("-" * 20)
            log.debug("")

        def uniq_name(name):
            if name in name_dict:
                name_dict[name] += 1
                return name + "_" + str(name_dict[name])
            else:
                name_dict[name] = 0
                return name

        self.devices = devices
        self.name = name

        log.info("Build fabric for".format(name))
        log.info("Device Heirachy test")

        # replaces a [] list with a sub fabric recursivly.
        for pos, d in enumerate(self.devices):
            # print(pos,d)
            if isinstance(d, list):
                log.critical("")
                log.critical("ENTER SUB FABRIC >>")
                # print(d)
                fb2 = FabricBuilder(d, name=uniq_name(self.name))
                # print(fb2)
                self.devices[pos] = fb2
                log.critical("<< LEAVE SUB FABRIC")
                log.critical("")

        log.debug("")
        log.debug("Device Scan")
        log.debug("address in halfwords")
        div()

        # Check for boot device save for address extraction

        boot_device = None
        # add attrs to the python objects
        for d in self.devices:
            d.name = uniq_name(d.__class__.__qualname__)
            d.width = d.bus.cmd.payload.addr.shape().width
            log.debug(f"{d.name} - {d.width}")
            if isinstance(d, BootMem):
                boot_device = d

        # log.critical("BIT ADDED HERE !")
        self.addr_width = addr_width = max(d.width for d in self.devices) + 1
        self.extra_bits = extra_bits = (len(self.devices) - 1).bit_length()

        log.debug("bus width %d ", self.addr_width)
        log.debug("bus extra bits %d ", self.extra_bits)
        log.debug(f"total width {addr_width+extra_bits}")
        div()

        # Create the memory map for the fabric itself
        self.memory_map = memory_map = MemoryMap(
            addr_width=addr_width + extra_bits + 1,
            data_width=16,
            name=uniq_name(name),
            alignment=addr_width,
        )

        # build the memory map list
        log.debug("Build the memory_map")
        for d in devices:
            log.debug(d.name)
            if hasattr(d, "memory_map"):
                log.critical("Device already has map")
                log.critical(d)
                memory_map.add_window(d.memory_map)
            else:
                device_memory = MemoryMap(
                    addr_width=d.width + 1, data_width=16, name=uniq_name(d.name)
                )
                # the size of the window may not be the same as the resource
                # memory may have less address values than bits that it has (after much prognostication) :)
                # it does have a bus width though...
                if hasattr(d, "size"):
                    res_size = d.size << 1
                else:
                    res_size = 2 ** (d.width + 1)
                device_memory.add_resource(d, name=(d.name,), size=res_size)
                memory_map.add_window(device_memory)

        # show the memory map
        div()
        for i in self.memory_map.window_patterns():
            log.debug(f"{i[0]} \t  {i[1][0]}, {len(i[1][0])}")
        # show the resources
        log.info("")
        log.info("Resources")
        div()
        for i in self.memory_map.all_resources():
            log.info(f"{i.path} \t{i.start} \t{i.end}")

        # self.bus = BusPort(addr=addr_width + extra_bits - 1, data=16).flip().create()

        # set some variables for the cpu to use

        self.addr_width = addr_width + extra_bits
        self.decoder_width = addr_width - 1

        if boot_device != None:
            # in half words
            self.reset_vector = memory_map.find_resource(boot_device).start >> 1
        else:
            self.reset_vector = 0  # main mem boot

    def bind(self, m):
        dev_list = []
        for dev in self.devices:
            dev_list.append(partial_decode(m, dev.bus, self.decoder_width))
        m.submodules.simple_fabric = fabric = SimpleFabric(dev_list)
        self.bus = fabric.bus

    def elaborate(self, platform):

        #log.warning("Elaborate Bus")
        m = Module()
        for dev in self.devices:
            m.submodules[dev.name] = dev
        return m
