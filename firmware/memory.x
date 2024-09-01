/*
 * Automatically generated by PATINA; edits will be discarded on rebuild.
 * (Most header files phrase this 'Do not edit.'; be warned accordingly.)
 *
 * Generated: 2024-09-01 11:20:13.315041.
 */

MEMORY {
    MEMORY : ORIGIN = 0x00000000, LENGTH = 0x1000
    BOOTMEM : ORIGIN = 0x00001000, LENGTH = 0x400
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
}
        

