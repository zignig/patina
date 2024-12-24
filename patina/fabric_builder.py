from functools import reduce

from amaranth import *
from amaranth.lib.wiring import *
from amaranth.lib.enum import *
from amaranth.lib.coding import Encoder, Decoder

from amaranth_soc.memory import MemoryMap

from hapenny import StreamSig, AlwaysReady, treeduce
from hapenny.serial import BidiUart
from hapenny.bus import SimpleFabric, partial_decode, BusPort
from hapenny.mem import BasicMemory

import subprocess
import os
import logging

log = logging.getLogger(__name__)


class BootMem(BasicMemory):
    """A subclass of the Basic mem for the bootloader"""

    def __init__(self,contents=None):
        # The boot image weighs in at 496 bytes
        # fits into one bram (on ice40)
        super().__init__(depth=512, read_only=True,contents=contents)

    # Name is set below in the fabric build
    def set_name(self, stack_start, uart_start):
        self.file_name = f"bootloader/bl-{stack_start}-{uart_start}.bin"

    def build(self):
        # build the firmware
        # split into two 
        log.critical(f'building -- {self.file_name}')
        file_parts = self.file_name.split(os.sep)
        self.folder = file_parts[0]
        self.bin_name = file_parts[1]
        r = subprocess.run(["cargo", "build", "--release"], cwd=self.folder)
        if r.returncode != 0:
            return False
        # convert to binary
        r = subprocess.run(
            ["cargo", "objcopy", "--release", "--", "-O", "binary", self.bin_name],
            cwd="bootloader",
        )
        if r.returncode != 0: 
            return False
        return True


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

        log.debug("Build fabric for".format(name))
        log.debug("Device hierarchy test")

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

        # Check for devices save for address extraction
        # used to build the firmware name
        boot_device = None
        uart_device = None
        last_mem = None
        # add attrs to the python objects
        for d in self.devices:
            d.name = uniq_name(d.__class__.__qualname__)
            d.width = d.bus.cmd.payload.addr.shape().width
            log.debug(f"{d.name} - {d.width}")
            if isinstance(d, BootMem):
                boot_device = d
            if isinstance(d, BidiUart):
                uart_device = d

        # Add extra bit to the address space for reasons
        self.addr_width = addr_width = max(d.width for d in self.devices) + 1
        # How many devices
        self.extra_bits = extra_bits = (len(self.devices) - 1).bit_length()

        log.debug("----")
        log.debug("bus width %d ", self.addr_width)
        log.debug("bus extra bits %d ", self.extra_bits)
        log.debug(f"total width {addr_width+extra_bits}")
        div()

        # Create the memory map for the fabric itself
        # Primic memory bus for the fabric
        self.memory_map = memory_map = MemoryMap(
            addr_width=addr_width + extra_bits + 1,
            data_width=16,
            alignment=addr_width,
        )
        storage_map = MemoryMap(addr_width=13,data_width=16)
        device_map = MemoryMap(addr_width=4,data_width=16)
        # build the memory map list
        log.debug("Build the memory_map")
        for i,d in enumerate(devices):
            log.debug(f"{i} - {d.name}")
            if hasattr(d, "memory_map"):
                log.critical("Device already has map")
                log.critical(d)
                memory_map.add_window(d.memory_map)
            else:
                device_memory = MemoryMap(
                    addr_width=d.width + 1, data_width=16
                )
                # the size of the window may not be the same as the resource
                # memory may have less address values than bits that it has
                # (after much prognostication) :) , tell me how I know.
                # it does have a bus width though...
                # TODO fold back into happenny.
                if hasattr(d, "depth"):
                    res_size = d.depth << 1
                else:
                    res_size = 2 ** (d.width + 1)
                device_memory.add_resource(d, name=d.name, size=res_size)
                memory_map.add_window(device_memory,name=d.name)


        #show the memory map
        div()
        for i in self.memory_map.window_patterns():
            log.info(f"{i[1][0].ljust(15)}{str(i[2]):^}")
            #log.info(f"{i[0]} \t  {i[1][0]}, {len(i[1][0])}")
        # show the resources
        # log.info("")
        # log.info("Resources")
        # div()
        # for i in self.memory_map.all_resources():
        #     log.info(f"{i.path} \t{i.start} \t{i.end}")

        # set some variables for the cpu to use

        self.addr_width = addr_width + extra_bits
        self.decoder_width = addr_width - 1

        # Articulate the boot device.
        # cargo build a "(stack)-(uart).bin" in this place
        # TODO make the bootloader dev free, please.
        if boot_device != None:
            stack_start = memory_map.find_resource(boot_device).start
            uart_start = memory_map.find_resource(uart_device).start

            boot_device.set_name(stack_start, uart_start)

            # in half words
            self.reset_vector = stack_start >> 1
        else:
            self.reset_vector = 0  # main mem boot

    def show(self):
        for i in self.memory_map.all_resources():
            log.info(f"{i.path} \t{i.start} \t{i.end}")

    def bind(self, m):
        """
        TODO make this into a multiplexor interface, slice the lower bit.
        """
        dev_list = []
        for dev in self.devices:
            dev_list.append(partial_decode(m, dev.bus, self.decoder_width))
        m.submodules.simple_fabric = fabric = SimpleFabric(dev_list)
        self.bus = fabric.bus

    def elaborate(self, platform):
        """
        This just adds submodules and does @cbiffles simple fabric

        TODO use a multiplexer instead rather than the simple fabric build
        """
        m = Module()
        for dev in self.devices:
            m.submodules[dev.name] = dev
        return m
