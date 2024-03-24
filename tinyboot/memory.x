/*
 * Automatically generated by PATINA; edits will be discarded on rebuild.
 * (Most header files phrase this 'Do not edit.'; be warned accordingly.)
 *
 * Generated: 2024-03-24 21:05:30.781812.
 */

MEMORY {
    MEM : ORIGIN = 0x00000000, LENGTH = 0x2000
    BOOT : ORIGIN = 0x00002000, LENGTH = 0x200
}


    
    EXTERN(__start);
    ENTRY(__start);

SECTIONS {
    PROVIDE(__stack_start = ORIGIN(MEM) + LENGTH(MEM));
    PROVIDE(__stext = ORIGIN(BOOT));

    .text __stext : {
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > BOOT

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    } > BOOT

    /DISCARD/ : {
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
    }
}
    

