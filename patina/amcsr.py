
from amaranth import *
from amaranth.lib.wiring import *

from amaranth_soc import csr

from hapenny import StreamSig, AlwaysReady, mux, oneof
from hapenny.bus import BusPort

class Amcsr_bus(Component):
    def __init__(self):
        