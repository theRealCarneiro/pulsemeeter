#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

from . import MainWindow
from . import Pulse

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk
from .settings import CONFIG_PATH

PIDFILE = '/tmp/pulsemeeter.pid'

def is_running():
    try:
        with open(PIDFILE) as f:
            pid = int(next(f))
        return os.kill(pid, 0)
    except Exception:
        return False

def main():
    config_orig='{"a": {"1": {"name": "", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "2": {"name": "", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "3": {"name": "", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}}, "b": {"1": {"name": "Mic", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "2": {"name": "Mic_Aux", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "3": {"name": "Mic_Aux_2", "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}}, "vi": {"1": {"name": "Virtual_Sink", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "2": {"name": "Virtual_Sink_Aux", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}, "3": {"name": "Virtual_Sink_Aux_2", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false}}, "hi": {"1": {"name": "", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false, "use_rnnoise": false, "rnnoise_name": "", "rnnoise_control": 95, "rnnoise_latency": 200}, "2": {"name": "", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false, "use_rnnoise": false, "rnnoise_name": "", "rnnoise_control": 95, "rnnoise_latency": 200}, "3": {"name": "", "a1": false, "a2": false, "a3": false, "b1": false, "b2": false, "b3": false, "a1_latency": 200, "a2_latency": 200, "a3_latency": 200, "b1_latency": 200, "b2_latency": 200, "b3_latency": 200, "vol": 100, "mute": false, "eq_control": "", "eq_name": "", "use_eq": false, "use_rnnoise": false, "rnnoise_name": "", "rnnoise_control": 95, "rnnoise_latency": 200}}}'
    config_orig = json.loads(config_orig)
    config_file = CONFIG_PATH
    config = None
    if not os.path.isfile(config_file):
        config = config_orig
        with open(config_file, 'w') as outfile:
            json.dump(config, outfile, indent='\t', separators=(',', ': '))
    else:
        config = json.load(open(config_file))
        changed = False
        for i in ['a', 'b', 'vi', 'hi']:
            for j in ['1', '2', '3']:
                for k in config_orig[i][j]:
                    if not k in config[i][j]:
                        changed = True
                        config[i][j][k] = config_orig[i][j][k]
        if changed == True:
            with open(config_file, 'w') as outfile:
                json.dump(config, outfile, indent='\t', separators=(',', ': '))
    pulse = Pulse(config)
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        exit()
    app = MainWindow(pulse)
    return Gtk.main()


if __name__ == '__main__':
    if is_running() != False:
        print('Another copy is already running')
        sys.exit(0)
    with open(PIDFILE, 'w') as f:
        f.write(f'{os.getpid()}\n')
    mainret = main()
    sys.exit(mainret)
