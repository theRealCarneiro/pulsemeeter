import os
import signal
import json
import sys

from .settings import PIDFILE
from . import MainWindow
from . import Pulse

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

def arg_interpreter(argv, pulse):
    if len(argv) <= 1:
        return

    if argv[1] == 'init':
        sys.exit(0)

    elif argv[1] == 'connect' or argv[1] == 'disconnect':
        pulse.connect(argv[1], [argv[2], argv[3]], [argv[4], argv[5]])

    elif argv[1] == 'rnnoise':
        pulse.rnnoise([argv[3], argv[4]], argv[5], argv[2])

    elif argv[1] == 'eq':
        if argv[2] == 'activate':
            pulse.apply_eq([argv[3], argv[4]])
        elif argv[2] == 'remove':
            pulse.remove_eq([argv[3], argv[4]])

    elif argv[1] == 'mute':
        state = argv[4] if len(argv) == 5 else None
        pulse.mute([argv[2], argv[3]], state)

    elif argv[1] == 'vol':
        pulse.volume([argv[2], argv[3]], argv[4])

    pulse.save_config()
    sys.exit(0)

def main():
    if len(sys.argv) == 1 or sys.argv[1] == 'init':
        is_running()
        pulse = Pulse()
    else:
        pulse = Pulse('cmd')
    arg_interpreter(sys.argv, pulse)
    app = MainWindow(pulse)
    return Gtk.main()

if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
