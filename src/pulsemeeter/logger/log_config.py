import os
import logging
import logging.config
from dataclasses import dataclass

from pulsemeeter import settings
# from pulsemeeter.logger.logger_config_dict import config


@dataclass
class Colors:
    GREY = '\x1b[38;21m'
    YELLOW = '\x1b[33;21m'
    RED = '\x1b[31;21m'
    RESET = '\x1b[0m'


CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "()": "pulsemeeter.logger.log_config.FormatLog",
            "format": "[%(levelname)s]: %(message)s",
            "datefmt": "%H:%M:%S"
        },

        "default": {
            "()": "pulsemeeter.logger.log_config.FormatLog",
            "format": "[%(asctime)s] [%(levelname)s]: %(message)s",
            "datefmt": "%H:%M:%S"
        },

        "debug": {
            "()": "pulsemeeter.logger.log_config.FormatLog",
            "format": "[%(asctime)s] [%(levelname)s] in [%(module)s@%(funcName)s]: %(message)s",
            "datefmt": "%y/%m/%Y %H:%M:%S"
        },

        "plain": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] %(module)s@%(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },

    "filters": {
        "info_and_below": {
            "()": "pulsemeeter.logger.log_config.filter_maker",
            "max_level": "INFO"
        }
    },

    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "filters": ["info_and_below"]
        },

        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "default",
            "stream": "ext://sys.stderr"
        }
    },

    "loggers": {
        "root": {
            "level": "INFO",
            "handlers": ["stdout", "stderr"]
        },

        "generic": {
            "level": "INFO"
        }

    }
}


def init_logger():
    console_level = "DEBUG" if settings.DEBUG else "INFO"
    CONFIG["loggers"]["root"]["level"] = "DEBUG"
    CONFIG["loggers"]["generic"]["level"] = "DEBUG"
    CONFIG["handlers"]["stdout"]["level"] = console_level

    try:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        CONFIG["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "plain",
            "filename": settings.LOG_FILE,
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "encoding": "utf-8"
        }
        if "file" not in CONFIG["loggers"]["root"]["handlers"]:
            CONFIG["loggers"]["root"]["handlers"].append("file")
    except OSError:
        pass

    logging.config.dictConfig(CONFIG)


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
