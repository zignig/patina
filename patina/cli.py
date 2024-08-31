import argparse
from patina.generate import *
import logging
from rich import print
from rich.panel import Panel
from rich.console import Console

from patina.loader import MonTool

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

    console = runner.add_parser("console",description="Connect a serial console")

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
            do_console(construct)
        case None:
            print(Panel("load the firmware and run "))


def do_build(platform, construct):
    platform.build(construct, do_program=True)


def do_mapping(construct):
    construct.fabric.show()


def do_generate(construct):
    ra = RustArtifacts(construct, folder="bootloader")
    ra.make_bootloader()

def do_console(construct):
    if hasattr(construct,"serial"):
        log.critical(f"attach {construct.serial}")
        if hasattr(construct,"baud_rate"):
            log.critical(f"{construct.baud_rate}")
            mt= MonTool(port=construct.serial,baud=construct.baud_rate)
            mt.run(construct.firmware)
    else:
        log.critical("Serial port not defined , construct needs .serial")