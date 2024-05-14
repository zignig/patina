# Stuff TODO.

The intent of Patina is to replace blinky in amaranth. Given (most; LUT > 0x1000), drop a riscv32i control plane CPU. This means that we can put a software state machine upon it.

The base is minimual rust but if you insist on writing C++ or C  that will work aswell. 

There appears to be a lot of stuff to do. My brain has stalled,
so I should probably write a list.

1. fix print! and println! , rework.
2. rework the bootloader to timeout on serial and load from flash
3. Rewrite the simple fabric to a multiplexer
4. write an amaranth_soc <-> hapenny bus bridge.
5. look into the svd exporter (for embeded-hal)
6. auto generate bootloader
7. move the command line into patina/cli.py
8.  move the logging builder into patina/logging.py
9. clean up the flash lib
   1.  add u32 reader and iterator
   2.  add byte array loader
   3.  write unlock
   4.  address start offset and size guardrails


# TO-DONE

These are not TODO these are TODONE.

1. Write the flash image generator [working]
   1. a page of config  (256 bytes)
   2. 1st word length of program. ( after this page)
   3. second word is address of the data block...
