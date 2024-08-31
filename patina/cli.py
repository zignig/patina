import argparse
from patina.generate import *

def run(platform,construct):
    print("do stuff on ",construct)
    parser = argparse.ArgumentParser(
        prog="Patina Running on tinybx",
        description="riscv32i mini soc",
        epilog="awesome!",
    )
    runner  = parser.add_subparsers(dest="commands")

    prepare = runner.add_parser("prepare")

    build = runner.add_parser('build')
    
    mapping = runner.add_parser("mapping")

    generate = runner.add_parser("generate")

    args = parser.parse_args()

    match args.commands:
        case "prepare":
            print(args)
            print("build firmware and stuff")
        case "build":
            do_generate(construct)
            do_build(platform,construct)
        case "mapping":
            do_mapping(construct)
        case "generate":
            do_generate(construct)
        case None:
            print("load the firmware and run ")
    print(args)


def do_build(platform,construct):
    platform.build(construct, do_program=True)

def do_mapping(construct):
    construct.fabric.show()

def do_generate(construct):
    ra = RustArtifacts(construct, folder="bootloader")
    ra.make_bootloader()