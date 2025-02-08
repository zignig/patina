#
# This file was part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause
# lifted from https://github.com/greatscottgadgets/luna-soc ( 319901c )

"""Generate Rust support files for SoC designs."""

import datetime
import logging
from hapenny.mem import BasicMemory,SpramMemory
from ..fabric_builder import BootMem

log = logging.getLogger("Rust Resources Files")

class GenRust:
    def __init__(self, soc):
        self._soc = soc

    # - memory.x generation ---------------------------------------------------
    def generate_memory_x(self, file=None):
        """ Generate a memory.x file for the given SoC"""

        def emit(content):
            """ Utility function that emits a string to the targeted file. """
            print(content, file=file)

        # warning header
        emit("/*")
        emit(" * Automatically generated by PATINA; edits will be discarded on rebuild.")
        emit(" * (Most header files phrase this 'Do not edit.'; be warned accordingly.)")
        emit(" *")
        emit(f" * Generated: {datetime.datetime.now()}.")
        emit(" */")
        emit("")

        # memory regions
        regions = set()
        emit("MEMORY {")
        # Consolidate memory
        is_start = False
        start_addr = 0
        end_addr = 0
        for i in self._soc.fabric.memory_map.all_resources():
            res = i.resource
            if not isinstance(res,(BasicMemory,SpramMemory)):
                continue
            if isinstance(res,BootMem):
                continue
            #log.critical(res.name)
            #log.critical(f"{i.start:08x} -> {i.end:08x}")
            if not is_start:
                start_addr = i.start
                is_start = True
            end_addr = i.end
        #log.critical(f" Range {start_addr:08x} -> {end_addr:08x}")
        emit(f"    MEMORY : ORIGIN = 0x{start_addr:08x}, LENGTH = 0x{(end_addr-start_addr):0x}")

        # Add bootmem if it exists
        for i in self._soc.fabric.memory_map.all_resources():
            res = i.resource
            name = i.resource.name.upper()
            start = i.start
            sec_length = i.end - i.start
            if isinstance(res,(BootMem)):
                emit(f"    {name} : ORIGIN = 0x{start:08x}, LENGTH = 0x{sec_length:0x}")
            if not isinstance(res,(BasicMemory,SpramMemory)):
                continue
            regions.add(name)
        emit("}")
        emit("")   
        self.extra(regions,emit)
        emit("")

    def extra(self,regions,emit):
        chunk = """
EXTERN(__start);
ENTRY(__start);

SECTIONS {{
    PROVIDE(__stack_start = ORIGIN({mem}) + LENGTH({mem})-16);
    PROVIDE(__stext = ORIGIN({mem}));

    .text __stext : {{
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    }} > {mem}

    .rodata : ALIGN(4) {{
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    }} > {mem}

    .data :
    {{
    *(.data .data.*);
    }} > {mem}
    .heap (NOLOAD) : ALIGN(4)
    {{
        . = ALIGN(4);
        . = ALIGN(4);
        __sheap = .;
    }} > {mem}
}}
        """
        emit(chunk.format(mem="MEMORY"))    
        
class BootLoaderX(GenRust):
    def __init__(self,soc):
        super().__init__(soc)
    
    def extra(self,regions,emit):
        chunk = """
    
EXTERN(__start);
ENTRY(__start);

SECTIONS {{
    PROVIDE(__stack_start = ORIGIN({mem}) + LENGTH({mem}));
    PROVIDE(__stext = ORIGIN({boot}));

    .text __stext : {{
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    }} > {boot}

    .rodata : ALIGN(4) {{
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    }} > {boot}

    /DISCARD/ : {{
        /* throw away RAM sections to get a link error if they're used. */
        *(.bss);
        *(.bss.*);
        *(.data);
        *(.data.*);
        *(COMMON);
        *(.ARM.exidx);
        *(.ARM.exidx.*);
        *(.ARM.extab.*);
        *(.got);
    }}
}}
    """
        emit(chunk.format(mem="MEMORY",boot="BOOTMEM"))
