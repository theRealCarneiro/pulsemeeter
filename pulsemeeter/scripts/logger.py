import logging
import sys
import threading
from pulsemeeter.settings import LOGGING_FORMAT, LOGGING_FORMAT_DEBUG, DEBUG


def init_log(name):
    """
    init custom logger
    can be used if there should be multiple loggers in one file with different properties
    """
    log = logging.getLogger(name)
    log.propagate = 0
    # change depending on debug level
    if DEBUG is True:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(FormatLog())
    log.addHandler(console)
    log.debug('started logger instance %s at thread %s', log, threading.get_native_id())
    return log


class FormatLog(logging.Formatter):
    """used to color format the logs"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    reset = "\x1b[0m"
    if DEBUG is True:
        format_txt = LOGGING_FORMAT_DEBUG
    else:
        format_txt = LOGGING_FORMAT

    FORMATS = {
        logging.DEBUG: grey + format_txt + reset,
        logging.INFO: grey + format_txt + reset,
        logging.WARNING: yellow + format_txt + reset,
        logging.ERROR: red + format_txt + reset,
        logging.CRITICAL: red + format_txt + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
