#!/usr/bin/python
# Serial interface for uploading firmware to the hapenny
# bootloader


from serial.tools.miniterm import Miniterm
import serial

from enum import Enum
from pathlib import Path
import struct
import argparse
import configparser
import os

class Commands(Enum):
    call = 0
    write = 1
    read = 2
    load_a = 3
    load_c = 4
    ping = 5


class MonTool:
    def __init__(self, port="/dev/ttyUSB0", baud=57600):
        self.port = port
        self.baud = baud
        self.ser = serial.serial_for_url(port, baud, timeout=0.1)
        # self.ser.dtr = 0

    def attach(self):
        term = Miniterm(self.ser)
        term.set_rx_encoding("utf-8")
        term.set_tx_encoding("utf-8")
        term.exit_character = "\x1d"
        print("Attach console ^] to exit.")
        term.start()
        term.join(True)
        # send exit (control d)
        self.ser.write([0x04])
        print("exit console")

    def _cmd(self, cmd):
        self.ser.write([cmd.value])

    def _ack(self, exit=True):
        val = self.ser.read()
        if len(val) > 0:
            if val[0] == 0xAA:  # ack packet
                return True
        else:
            if exit:
                raise ("ack failed")
            else:
                return False

    def _flush(self):
        while True:
            val = self.ser.read()
            print(val)
            if val == b'':
                return
    
    def _write_num(self, val):
        num = val.to_bytes(4, byteorder="little")
        self.ser.write(num)

    def _read_num(self):
        data = self.ser.read(4)
        num = int.from_bytes(data, byteorder="little")
        return num

    def _write_a(self, val):
        self._cmd(Commands.load_a)
        self._write_num(val)

    def _write_c(self, val):
        self._cmd(Commands.load_c)
        self._write_num(val)

    def ping(self):
        self._flush()
        self._cmd(Commands.ping)
        val = self._ack(exit=False)
        return val

    def call(self, addr):
        self._write_a(addr)
        self._ack()
        self._cmd(Commands.call)
        self._ack()
        # jumps to program and runs

    def read(self, addr, count):
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

    def write(self, addr, data):
        count = len(data)
        print(addr, count * 4, " bytes")
        self._write_a(addr)
        self._ack()
        self._write_c(count)
        self._ack()
        self._cmd(Commands.write)
        for (count,val) in enumerate(data):
            if count % 20 == 0:
                print('#',end='')
            self._write_num(val)
        print()
        self._ack()

    def peek(self, addr):
        return self.read(addr, 1)

    def poke(self, addr, val):
        self.write(addr, val)

    def load(self, file_name):
        bootloader = Path(file_name).read_bytes()
        boot_image = struct.unpack("<" + "I" * (len(bootloader) // 4), bootloader)
        return list(boot_image)

    def run(self, file_name):
        print("Loading ", file_name)
        firm = m.load(file_name)
        m.write(0, firm)
        m.call(0)
        m.attach()


if __name__ == "__main__":
    import argparse

    cfile = "loader.conf"
    conf = configparser.ConfigParser()

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-b", "--baud", type=int)
    parser.add_argument("-f", "--firmware", type=str)
    parser.add_argument("-c", "--console", action="store_true")
    parser.add_argument("-s", "--save", action="store_true")

    args = parser.parse_args()

    # save the config file
    if args.save:
        settings = args.__dict__
        if "save" in settings:
            del settings["save"]
        conf.read_dict({"serial": settings})
        with open(cfile, "w") as config_file:
            conf.write(config_file)
        print("config saved")
    else:
        del args.save

    # load the config file
    try:
        os.stat(cfile)
        conf.read_file(open(cfile))
        conf_dict = dict(conf['serial'].items())
        args_dict = args.__dict__

        # use command line as override
        for i in args_dict.keys():
            if args_dict[i] is not None:
                #print("override",i)
                conf_dict[i] = args_dict[i]
        
        # create new args
        args = argparse.Namespace(**conf_dict)
    except:
        print("no config")
   
    #print(args)
    #print(conf_dict)
    
    # spin up the monitor
    m = MonTool(port=args.port, baud=args.baud)
    if m.ping():
        m.run(args.firmware)
    else:
        if args.console:
            m.attach()
        else:
            print()
            print('no active bootloader')
