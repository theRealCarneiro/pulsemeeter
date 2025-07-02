import os
import json
import logging
import logging.config
from dataclasses import dataclass

from pulsemeeter import settings


@dataclass
class Colors:
    GREY = '\x1b[38;21m'
    YELLOW = '\x1b[33;21m'
    RED = '\x1b[31;21m'
    RESET = '\x1b[0m'


def init_logger():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f'{script_dir}/logger_config.json', 'r', encoding='utf-8') as fp:
        config = json.load(fp)
        level = "DEBUG" if settings.DEBUG else "INFO"
        config["loggers"]["root"]["level"] = level
        config["loggers"]["generic"]["level"] = level
        logging.config.dictConfig(config)


class FormatLog(logging.Formatter):

    level_colors = {
        logging.DEBUG: Colors.GREY,
        logging.INFO: Colors.GREY,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED,
    }

    def format(self, record):
        '''
        Applies color coding to different log levels.
        '''
        format_color = self.level_colors.get(record.levelno, Colors.GREY)
        message = super().format(record)
        return format_color + message + Colors.RESET


def filter_maker(max_level):
    max_level = getattr(logging, max_level)

    def flt(record):
        return record.levelno <= max_level

    return flt
