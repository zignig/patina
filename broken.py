import os
import subprocess

from amaranth_boards.tinyfpga_bx import TinyFPGABXPlatform
from amaranth_boards.test.blinky import Blinky

TinyFPGABXPlatform().build(Blinky(), do_program=True)