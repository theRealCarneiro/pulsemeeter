import os


__version__ = '1.2.16'

# show/hide debug messages
DEBUG = True

HOME = os.getenv('HOME', os.getenv('USERPROFILE'))

USER = os.getenv('USER')
APP_DIR = os.path.dirname(os.path.realpath(__file__))
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', f'/home/{USER}/.config')
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
ORIG_CONFIG_FILE = os.path.join(APP_DIR, 'config.json')
LAYOUT_DIR = os.path.join(APP_DIR, 'interface/layouts')
GLADEFILE = os.path.join(LAYOUT_DIR, 'defaulth')
SOCK_FILE = f'/tmp/pulsemeeter.{USER}.sock'
PIDFILE = f'/tmp/pulsemeeter.{USER}.pid'
LISTENER_TIMEOUT = 2

# logging formats
# for vars look at: https://docs.python.org/3/library/logging.html#logrecord-attributes
LOGGING_FORMAT = "[%(levelname)s] in [%(module)s]: %(message)s"
LOGGING_FORMAT_DEBUG = "[%(levelname)s] in [%(module)s@%(funcName)s]: %(message)s"
