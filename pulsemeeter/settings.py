import os
import platform


__version__ = '1.2.2'


HOME = os.getenv('HOME', os.getenv('USERPROFILE'))

INSTALL_DIR = 'site-packages'
for i in ['/usr/lib/python3.9', '/usr/local/lib/python3.9', os.path.join(HOME, '.local/lib/python3.9')]:
    if os.path.exists(os.path.join(i, 'dist-packages')):
        INSTALL_DIR = 'dist-packages'
        break

CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
CONFIG_DIR = os.path.join(CONFIG_HOME, 'pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
ORIG_CONFIG_FILE = f'lib/python3.9/{INSTALL_DIR}/pulsemeeter/config.json'
GLADEFILE = f'lib/python3.9/{INSTALL_DIR}/pulsemeeter/Interface.glade'
PIDFILE = '/tmp/pulsemeeter.pid'
