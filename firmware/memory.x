/*
 * Automatically generated by PATINA; edits will be discarded on rebuild.
 * (Most header files phrase this 'Do not edit.'; be warned accordingly.)
 *
 * Generated: 2025-02-05 07:11:21.663054.
 */

MEMORY {
    MEMORY : ORIGIN = 0x00000000, LENGTH = 0x2800
    BOOTMEM : ORIGIN = 0x00004000, LENGTH = 0x400
}


EXTERN(__start);
ENTRY(__start);

SECTIONS {
    PROVIDE(__stack_start = ORIGIN(MEMORY) + LENGTH(MEMORY)-16);
    PROVIDE(__stext = ORIGIN(MEMORY));

    .text __stext : {
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > MEMORY

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    } > MEMORY

    .data :
    {
    *(.data .data.*);
    } > MEMORY
    .heap (NOLOAD) : ALIGN(4)
    {
        __sheap = .;
        . = ALIGN(4);
    } > MEMORY
}
        

