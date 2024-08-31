import argparse
from patina.generate import *
import logging
from rich import print
from rich.panel import Panel
from rich.console import Console

from patina.loader import MonTool

import subprocess

log = logging.getLogger(__name__)


def run(platform, construct):

    console = Console()

    print(Panel(f"Build the {construct.__class__.__name__}"))

    parser = argparse.ArgumentParser(
        prog="Patina Running on tinybx",
        description="riscv32i mini soc",
        epilog="awesome!",
    )
    runner = parser.add_subparsers(dest="commands")

    prepare = runner.add_parser("prepare")

    build = runner.add_parser("build")

    mapping = runner.add_parser("mapping")

    generate = runner.add_parser("generate")

    console = runner.add_parser("console", description="Connect a serial console")
    console.add_argument("-b", "--bin", type=str)

    args = parser.parse_args()
    
    match args.commands:
        case "prepare":
            print(Panel("build firmware and stuff"))
            do_mapping(construct)
        case "build":
            do_generate(construct)
            do_build(platform, construct)
        case "mapping":
            do_mapping(construct)
        case "generate":
            do_generate(construct)
        case "console":
            print(Panel("Attach the console.."))
            build_firmware(construct)
            do_console(construct)
        case None:
            do_generate(construct)
            do_console(construct)


def do_build(platform, construct):
    platform.build(construct, do_program=True)


def do_mapping(construct):
    construct.fabric.show()


def do_generate(construct):
    ra = RustArtifacts(construct, folder="bootloader")
    ra.make_bootloader()
    ra = RustArtifacts(construct, folder="firmware")
    ra.make_firmware()


def do_console(construct):
    if hasattr(construct, "serial"):
        if hasattr(construct, "baud_rate"):
            mt = MonTool(port=construct.serial, baud=construct.baud_rate)
            try:
                mt.run(construct.firmware)
            except:
                log.critical(f"Console Failed , no ack from {construct.serial}")
    else:
        log.critical("Serial port not defined , construct needs .serial")


def build_firmware(construct):
    if not hasattr(construct, "firmware"):
        log.critical(f"No firmware provided")
        return
    log.info(f"Build firmware {construct.firmware}")
    file_parts = construct.firmware.split(os.sep)
    folder = file_parts[0]
    bin_name = file_parts[1]
    r = subprocess.run(["cargo", "build", "--release", "--bin", bin_name], cwd=folder)
    if r.returncode != 0:
        return False
    # convert to binary
    r = subprocess.run(
        ["cargo", "objcopy", "--release", "--", "-O", "binary", bin_name],
        cwd="bootloader",
    )
