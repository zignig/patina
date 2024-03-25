#!/usr/bin/python
" Serial interface for uploading boneless firmware"


from serial.tools.miniterm import Miniterm
import serial

from enum import Enum
from pathlib import Path
import struct



the_port ="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A700eCzo-if00-port0"

class Commands(Enum):
    call = 0
    write = 1
    read = 2
    load_a  = 3
    load_c = 4
    ping = 5

class MonTool:
    def __init__(self, port, baud=57600):
        self.port = port
        self.baud = baud
        self.ser = serial.serial_for_url(
            port, baud
        )
        # self.ser.dtr = 0

    def attach(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("-l", "--list", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")

        args = parser.parse_args()
        term = Miniterm(self.ser)
        term.set_rx_encoding("utf-8")
        term.set_tx_encoding("utf-8")
        term.exit_character = "\x1d"
        print("Attach console")
        term.start()
        term.join(True)
    
    def _cmd(self,cmd):
        self.ser.write([cmd.value])
    
    def _ack(self):
        val = self.ser.read()
        if val[0] == 0xAA: # ack packet
            return True
        else:
            raise("fail")

    def _write_num(self,val):
        num = val.to_bytes(4,byteorder="little")
        self.ser.write(num)
    
    def _read_num(self):
        data = self.ser.read(4)
        num = int.from_bytes(data,byteorder="little")
        return num

    def _write_a(self,val):
        self._cmd(Commands.load_a)
        self._write_num(val)

    def _write_c(self,val):
        self._cmd(Commands.load_c)
        self._write_num(val)

    def ping(self):
        self._cmd(Commands.ping)
        self._ack()

    def call(self,addr):
        self._write_a(addr)
        self._ack()
        self._cmd(Commands.call)
        # does not return

    def read(self,addr,count):
        self._write_a(addr)
        self._ack()
        self._write_c(count)
        self._ack()
        self._cmd(Commands.read)
        self._ack()
        data = []
        for pos in range(count):
            val = self._read_num()
            data.append(val)
        return data

    def write(self,addr,data):
        count = len(data)
        print(addr,count)
        self._write_a(addr)
        self._ack()
        self._write_c(count)
        self._ack()
        self._cmd(Commands.write)
        for val in data:
            self._write_num(val)
        self._ack()

    def peek(self,addr):
        return self.read(addr,1)

    def poke(self,addr,val):
        self.write(addr,val)

    def load(self,file_name):
        bootloader = Path(file_name).read_bytes()
        boot_image = struct.unpack("<" + "I" * (len(bootloader) // 4), bootloader)
        return list(boot_image)


if __name__ == "__main__":
    m = MonTool(the_port)
    m.ping()
    m.load("tinybx8k.bin")