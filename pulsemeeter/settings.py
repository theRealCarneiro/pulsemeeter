import os
import platform
import appdirs
 

__version__ = '1.2.6'


HOME = os.getenv('HOME', os.getenv('USERPROFILE'))

APP_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = appdirs.user_config_dir('pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
ORIG_CONFIG_FILE = os.path.join(APP_DIR, 'config.json')
GLADEFILE = os.path.join(APP_DIR, 'Interface.glade')
PIDFILE = '/tmp/pulsemeeter.pid'
