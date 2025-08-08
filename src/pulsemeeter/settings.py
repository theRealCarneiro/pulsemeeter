'''
Settings for the runtime of pulsemeeter
'''
import gettext
import os


VERSION = '2.0.0'
APP_NAME = "pulsemeeter"

# config settings
USER = os.getenv('USER')
HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
XDG_DATA_HOME = os.getenv('XDG_DATA_HOME', os.path.join(HOME, '.local/share'))
XDG_RUNTIME_DIR = os.getenv('XDG_RUNTIME_DIR', '/tmp')
APP_RUNTIME_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'pulsemeeter')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
STYLE_FILE = os.path.join(CONFIG_DIR, 'style.css')

# IPC SETTINGS
LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5
SOCK_FILE = os.path.join(XDG_RUNTIME_DIR, f'pulsemeeter.{USER}.sock')
PIDFILE = os.path.join(XDG_RUNTIME_DIR, f'pulsemeeter.{USER}.pid')


# logging
DEBUG = False

# Translations
LOCALE_DIR = ''
LOCALE_DIRS = [
    '/usr/share/locale',
    '/usr/local/share/locale',
    os.path.join(APP_RUNTIME_DIR, "locale"),
    os.path.join(XDG_DATA_HOME, "locale")
]

# Search for translations
for locale_dir in LOCALE_DIRS:
    try:
        gettext.translation(APP_NAME, locale_dir)  # look for .mo files in path
        LOCALE_DIR = locale_dir  # set it when no exception is raised

    # ignore when we dont find it
    except FileNotFoundError:
        pass

gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
gettext.textdomain(APP_NAME)
