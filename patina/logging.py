# logging for 

import logging, sys

from rich.logging import RichHandler

log_level = logging.INFO

fomattingter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s \t  %(name)s - line %(lineno)s - (%(funcName)s)",
    datefmt="%Y%m%d %H:%M:%S",
)
# fomattingter = logging.Formatter( fmt="%(asctime)s - %(levelname)s %(name)s.%(funcName)s - %(message)s")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fomattingter)
root_logger = logging.getLogger()
root_logger.addHandler(RichHandler())
root_logger.setLevel(log_level)


def logger(name):
    return root_logger.getChild(name)


def set_logging_level(set_level):
    root_logger.setLevel(set_level)