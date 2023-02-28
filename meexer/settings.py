'''
Settings for the runtime of pulsemeeter
'''
import os


__version__ = '1.2.16'

# show/hide debug messages
DEBUG = True

# config settings
USER = os.getenv('USER')
HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# IPC SETTINGS
LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5
SOCK_FILE = f'/tmp/pulsemeeter.{USER}.sock'
PIDFILE = f'/tmp/pulsemeeter.{USER}.pid'


# logging formats
# for vars look at:
# https://docs.python.org/3/library/logging.html#logrecord-attributes
LOGGING_FORMAT = "[%(levelname)s] in [%(module)s]: %(message)s"
LOGGING_FORMAT_DEBUG = "[%(levelname)s] in [%(module)s@%(funcName)s]: %(message)s"
