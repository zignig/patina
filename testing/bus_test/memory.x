MEMORY {
    RAMA (rw): ORIGIN = 0, LENGTH = 512
    RAMB (rw): ORIGIN = 512, LENGTH = 512
}

EXTERN(__start);
ENTRY(__start);

SECTIONS {
    PROVIDE(__stack_start = ORIGIN(RAMA) + LENGTH(RAMA));

    PROVIDE(__stext = ORIGIN(RAMA));

    .text __stext : {
        *(.start);

        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > RAMA

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;
        *(.rodata .rodata.*);
        . = ALIGN(4);
        __erodata = .;
    } > RAMA

    .data :
    {
    *(.data .data.*);
    } > RAMA

    
    .eh_frame (INFO) : { KEEP(*(.eh_frame)) }

}
