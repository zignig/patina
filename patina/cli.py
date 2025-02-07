import argparse
from patina.generate import *
import logging
from rich import print
from rich.panel import Panel
from rich.console import Console

from patina.loader import MonTool

import subprocess

log = logging.getLogger(__name__)


def panel(data):
    print(Panel(data))


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
    console.add_argument("bin", nargs="?", type=str)

    deploy = runner.add_parser("deploy")
    svd = runner.add_parser("svd")

    args = parser.parse_args()

    match args.commands:
        case "prepare":
            panel("build firmware and stuff")
            do_mapping(construct)
        case "build":
            do_generate(construct)
            do_build(platform, construct)
        case "mapping":
            do_mapping(construct)
        case "generate":
            do_generate(construct)
        case "console":
            panel("Attach the console..")
            log.critical(args)
            build_firmware(construct, args.bin)
            do_console(construct,args.bin)
        case "deploy":
            do_generate(construct)
            do_build(platform, construct)
            build_firmware(construct)
            do_console(construct)
        case "svd":
            do_svd(construct)
        case None:
            do_build(platform, construct)
            do_console(construct)


def do_build(platform, construct):
    panel("Building FPGA image ; pls hold ...")
    platform.build(construct, do_program=True)


def do_mapping(construct):
    construct.fabric.show()


def do_generate(construct):
    ra = RustArtifacts(construct)
    ra.make_bootloader("bootloader")
    #ra.make_firmware("firmware")
    ra.make_firmware("patina_pac")
    

def do_svd(construct):
    ra = RustArtifacts(construct)
    ra.make_svd('.')

def do_console(construct,bin_name=None):
    if hasattr(construct, "serial"):
        if hasattr(construct, "baud"):
            if bin_name is None:
                bin_name=construct.firmware[1]
            mt = MonTool(port=construct.serial, baud=construct.baud)
            name = "/".join([construct.firmware[0],'bin',bin_name])
            mt.run(name)
            # try:
            #     mt.run(construct.firmware)
            # except:
            #     log.critical(f"Console Failed , no ack from {construct.serial}")
    else:
        log.critical("Serial port not defined , construct needs .serial")


def build_firmware(construct, bin_name=None):
    if hasattr(construct, "firmware"):
        if construct.firmware is not None:
            log.info(f"Build firmware {construct.firmware}")
            folder = construct.firmware[0]
            if bin_name is None:
                bin_name = construct.firmware[1]
            r = subprocess.run(
                ["cargo", "build", "--release", "--bin", bin_name], cwd=folder
            )
            if r.returncode != 0:
                log.critical("Firmware failed")
            # convert to binary
            r = subprocess.run(
                [
                    "cargo",
                    "objcopy",
                    "--release",
                    "--bin",
                    bin_name,
                    "--",
                    "-O",
                    "binary",
                    f"bin/{bin_name}",
                ],
                cwd=folder,
            )
        else:
            log.critical("Firmware is none")
    else:
        log.critical(f"No firmware provided")
        return
