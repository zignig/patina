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


class ProgramMemory(BasicMemory):
    """A subclass of the Basic mem for the bootloader"""

    def __init__(self, depth=512, contents=None):
        # The boot image weighs in at 496 bytes
        # fits into one bram (on ice40)
        super().__init__(depth=depth, contents=contents, read_only=True)

    # Name is set below in the fabric build
    def set_file(self, file_name):
        self.file_name = file_name

    def build(self):
        # build the firmware
        # split into two
        log.critical(f"building -- {self.file_name}")
        file_parts = self.file_name.split(os.sep)
        self.folder = file_parts[0]
        self.bin_name = file_parts[2]
        log.critical(f"folder -- { self.folder }")

        # build the elf file
        r = subprocess.run(
            ["cargo", "build", "--release", "--bin", self.bin_name],
            cwd=self.folder,
        )
        if r.returncode != 0:
            return False
        log.critical(f"binary name -- { self.bin_name }")
        # convert to binary
        r = subprocess.run(
            ["cargo", "objcopy", "--release","--bin", self.bin_name ,"--", "-O", "binary", self.bin_name],
            cwd=self.folder,
        )
        if r.returncode != 0:
            print(r.stdio)
            return False
        return True


class BootMem(ProgramMemory):
    def __init__(self, depth=512, contents=None):
        super().__init__(depth=depth, contents=contents)


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

        # Check for specific devices and save for address extraction
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

        # Add extra bit to the address space beacuse it's in 16 bit half words
        self.addr_width = addr_width = max(d.width for d in self.devices) + 1
        # How many devices
        self.extra_bits = extra_bits = (len(self.devices) - 1).bit_length()

        log.debug("----")
        log.debug("bus width %d ", self.addr_width)
        log.debug("bus extra bits %d ", self.extra_bits)
        log.debug(f"total width {addr_width+extra_bits}")
        div()

        # Create the memory map for the fabric itself
        # the alignment pushes all the bits left so it
        # matches the elaborated bus
        self.memory_map = memory_map = MemoryMap(
            addr_width=addr_width + extra_bits + 1,
            data_width=16,
            alignment=addr_width,
        )

        # build the memory map list
        log.debug("Build the memory_map")
        for i, d in enumerate(devices):
            log.debug(f"{i} - {d.name}")

            if hasattr(d, "memory_map"):
                # log.critical("Device already has map")
                #  log.critical(d)
                memory_map.add_window(d.memory_map, name=d.name, sparse=True)
            else:
                device_memory = MemoryMap(addr_width=d.width + 1, data_width=16)
                # the size of the window may not be the same as the resource
                # memory may have less address values than bits that it has
                # (after much prognostication) :) , ask me how I know.
                # it does have a bus width though...
                if hasattr(d, "depth"):
                    res_size = d.depth << 1
                else:
                    res_size = 2 ** (d.width + 1)
                device_memory.add_resource(d, name=d.name, size=res_size)
                memory_map.add_window(device_memory, name=d.name)

        # set some variables for the cpu to use

        self.addr_width = addr_width + extra_bits
        self.decoder_width = addr_width - 1

        # Articulate the boot device.
        # cargo build a "(stack)-(uart).bin" in this place
        # TODO make the bootloader dev free, please.
        if boot_device != None:
            stack_start = memory_map.find_resource(boot_device).start
            uart_start = memory_map.find_resource(uart_device).start
            # Set the name of the boot mem
            # if this file does not exist it will compile on
            # elaboration
            boot_device.set_file(f"bootloader/bin/bl-{stack_start}-{uart_start}.bin")

            # in half words
            self.reset_vector = stack_start >> 1
        else:
            self.reset_vector = 0  # main mem boot

        # Gen some info ( moved from hapenny/bus.py)
        assert len(devices) > 0
        data_bits = max(p.bus.cmd.payload.data.shape().width for p in devices)
        addr_bits = max(p.bus.cmd.payload.addr.shape().width for p in devices)
        sig = BusPort(addr=addr_bits, data=data_bits).flip()
        log.info(f"fabric configured for {addr_bits} addr bits, {data_bits} data bits")
        self.extra_bits = (len(devices) - 1).bit_length()
        self.addr_bits = addr_bits
        self.data_bits = data_bits

        # Create the actual bus device
        self.bus = (
            BusPort(addr=addr_bits + self.extra_bits, data=data_bits).flip().create()
        )

    def show(self):
        # TODO make this fancy
        for i in self.memory_map.all_resources():
            log.info(f"{i.path} \t{i.start} \t{i.end}")

    def elaborate(self, platform):
        """
        Create The fabric
        """
        m = Module()
        # Attach all the sub modules
        for dev in self.devices:
            m.submodules[dev.name] = dev

        # create the partials
        dev_list = []
        for dev in self.devices:
            dev_list.append(partial_decode(m, dev.bus, self.decoder_width))

        # Copied from hapenny/bus.py

        devid = Signal(self.extra_bits)
        m.d.comb += devid.eq(self.bus.cmd.payload.addr[self.addr_bits :])

        # index of the last selected device (registered).
        last_id = Signal(self.extra_bits)
        # Since the setting of the response mux is ignored if the CPU isn't
        # expecting data back, we can just capture the address lines on every
        # cycle whether it's valid or not.
        m.d.sync += last_id.eq(devid)

        for i, d in enumerate(dev_list):
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
            data = d.bus.resp & (last_id == i).replicate(self.data_bits)
            response_data.append(data)

        m.d.comb += self.bus.resp.eq(treeduce(lambda a, b: a | b, response_data))

        return m
