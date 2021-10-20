import os
import platform


__version__ = '1.1'


HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
CONFIG_PATH = os.path.join(CONFIG_HOME, 'pulsemeeter/config.json')
GLADEFILE = 'lib/python3.9/site-packages/pulsemeeter/Interface.glade'

OS = platform.uname()[0]
