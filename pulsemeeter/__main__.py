import os
import signal
import json
import sys

from .settings import PIDFILE
from . import MainWindow
from . import Pulse
from . import Client, Server

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk

def is_running():
    try:
        with open(PIDFILE) as f:
            pid = int(next(f))
        if os.kill(pid, 0) != False:
            print('Another copy is already running')
            sys.exit(0)
        else:
            with open(PIDFILE, 'w') as f:
                f.write(f'{os.getpid()}\n')
    except Exception:
        with open(PIDFILE, 'w') as f:
            f.write(f'{os.getpid()}\n')

def arg_interpreter(argv, pulse, loglevel):
    if len(argv) <= 1 or loglevel > 0:
        return

    # if argv[1] == 'init':
        # sys.exit(0)


    # elif argv[1] == 'connect' or argv[1] == 'disconnect':
        # pulse.connect(argv[1], [argv[2], argv[3]], [argv[4], argv[5]])

    # elif argv[1] == 'rnnoise':
        # pulse.rnnoise([argv[3], argv[4]], argv[5], argv[2])

    # elif argv[1] == 'eq':
        # if argv[2] == 'activate':
            # pulse.apply_eq([argv[3], argv[4]])
        # elif argv[2] == 'remove':
            # pulse.remove_eq([argv[3], argv[4]])

    # elif argv[1] == 'mute':
        # state = argv[4] if len(argv) == 5 else None
        # pulse.mute([argv[2], argv[3]], state)

    # elif argv[1] == 'vol':
        # pulse.volume([argv[2], argv[3]], argv[4])

    # pulse.save_config()
    # sys.exit(0)

def main():
    loglevel = 0
    if 'loglevel-all' in sys.argv:
        loglevel = 2
    if 'loglevel-error' in sys.argv:
        loglevel = 1
        
    pulse = Pulse(loglevel=loglevel)
    if sys.argv[1] == 'server':
        Server(pulse)
    else:
        Client()

    # if len(sys.argv) == 1 or sys.argv[1] == 'init' or loglevel > 0:
        # is_running()
        # pulse = Pulse(loglevel=loglevel)
    # else:
        # pulse = Pulse('cmd', loglevel=loglevel)

    # arg_interpreter(sys.argv, pulse, loglevel)

    # while True:
        # app = MainWindow(pulse)
        # Gtk.main()
        # if pulse.restart_window == False:
            # break

if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
