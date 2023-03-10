'''
Settings for the runtime of pulsemeeter
'''
import os


VERSION = '1.2.16'

# config settings
USER = os.getenv('USER')
HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
XDG_RUNTIME_DIR = os.getenv('XDG_RUNTIME_DIR', '/tmp')
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# IPC SETTINGS
LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5
SOCK_FILE = os.path.join(XDG_RUNTIME_DIR, f'pulsemeeter.{USER}.sock')
PIDFILE = os.path.join(XDG_RUNTIME_DIR, f'pulsemeeter.{USER}.pid')


# logging
DEBUG = True
LOGGING_FORMAT = "[%(levelname)s] in [%(module)s]: %(message)s"
LOGGING_FORMAT_DEBUG = "[%(levelname)s] in [%(module)s@%(funcName)s]: %(message)s"
