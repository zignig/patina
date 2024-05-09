# Stuff TODO.

There appears to be a lot of stuff to do. My brain has stalled,
so I should probably write a list.

1. Write the flash image generator
2. rework the bootloader to timeout on serial and load from flash
3. Rewrite the simple fabric to a multiplexer
4. write an amaranth_soc <-> hapenny bus bridge.
5. look into the svd exporter (for embeded-hal)
6. auto generate bootloader
7. move the command line into patina/cli.py
8. move the logging builder into patina/logging.py
9. clean up the flash lib
   1.  add u32 reader and iterator
   2.  add byte array loader
   3.  write unlock
   4.  address start offset and size guardrails
