import os
import platform
import appdirs
 

__version__ = '1.2.12'


HOME = os.getenv('HOME', os.getenv('USERPROFILE'))

USER = os.getenv('USER')
APP_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = appdirs.user_config_dir('pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
ORIG_CONFIG_FILE = os.path.join(APP_DIR, 'config.json')
LAYOUT_DIR = os.path.join(APP_DIR, 'interface/layouts')
GLADEFILE = os.path.join(APP_DIR, 'interface/layouts/Tabbed.glade')
SOCK_FILE = f'/tmp/pulsemeeter.{USER}.sock'
PIDFILE = f'/tmp/pulsemeeter.{USER}.pid'
