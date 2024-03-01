MEMORY {
    #PROGMEM (rw): ORIGIN = 0x2000, LENGTH = 512
    RAM (rwx): ORIGIN = 0x0000, LENGTH = 0x2000
}

EXTERN(__start);
ENTRY(__start);

SECTIONS {
    PROVIDE(__stack_start = ORIGIN(RAM) + LENGTH(RAM)-16);

    PROVIDE(__stext = ORIGIN(RAM));

    .text __stext : {
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > RAM

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    } > RAM

    .data :
    {
    *(.data .data.*);
    } > RAM

    
    .eh_frame (INFO) : { KEEP(*(.eh_frame)) }

}
