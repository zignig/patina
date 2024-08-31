# logging for

import logging, sys

from rich.logging import RichHandler

log_level = logging.DEBUG
FORMAT = "%(message)s" #\t  %(name)s - line %(lineno)s - (%(funcName)s)"
handler = RichHandler()

logging.basicConfig(
    level=log_level, format=FORMAT, datefmt="%S", handlers=[handler]
)
