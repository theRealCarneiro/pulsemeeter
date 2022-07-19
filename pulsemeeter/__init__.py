from .interface import MainWindow
from .backends import *
from .socket import *
from .settings import __version__
from .logger import init_log

init_log("generic")

__all__ = [
    '__version__',
]
