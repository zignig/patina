# logging for

import logging, sys

from rich.logging import RichHandler

log_level = logging.INFO


FORMAT = "%(message)s" #\t  %(name)s - line %(lineno)s - (%(funcName)s)"
handler = RichHandler()

lg = logging.basicConfig(
    level=log_level, format=FORMAT, datefmt="%S", handlers=[handler]
)
