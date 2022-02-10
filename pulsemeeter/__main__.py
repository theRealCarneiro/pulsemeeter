import os
import signal
import json
import sys
import argparse
# import re

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

def str_to_bool(string, parser):
        if type(string) == bool: return string 
        else:
            if string.lower() in ['true', '1', 'on']: return True
            elif string.lower() in ['false', '0', 'off']: return False

# ----------------
# Parser generators 
# ----------------
device_arg = {'type': int}

def parser_generic(parser ,value_type, source, sink):
    if source == True or sink == True:
        device = parser.add_mutually_exclusive_group(required=True)
    if source == True:
        device.add_argument('-vi', '--virtual-input', **device_arg)
        device.add_argument('-hi', '--hardware-input', **device_arg)
    if sink == True:
        device.add_argument('-a', **device_arg)
        device.add_argument('-b', **device_arg)
    if value_type != None:
        parser.add_argument('value', type=value_type, default=None, nargs='?')

def parser_only_value(parser, value_type):
    parser.add_argument('value', type=value_type, default=None ,nargs='?')

def parser_source_to_sink(parser, value_type):
    in_device = parser.add_mutually_exclusive_group(required=True)
    in_device.add_argument('-vi', '--virtual-input', **device_arg)
    in_device.add_argument('-hi', '--hardware-input', **device_arg)
    out_device = parser.add_mutually_exclusive_group(required=True)
    out_device.add_argument('-a', **device_arg)
    out_device.add_argument('-b', **device_arg)
    parser.add_argument('value', type=value_type, default=None, nargs='?')

# ----------------

def create_parser_args(c):
    parser = argparse.ArgumentParser(description='Replicating voicemeeter routing functionalities in linux with pulseaudio')

    # Parser_generic = [parser] [value_type] [source] [sink]
    subparsers = parser.add_subparsers(dest='command')
    parser_source_to_sink(subparsers.add_parser('connect'), str)
    # primary
    parser_generic(subparsers.add_parser('mute'), str, True, True)
    parser_generic(subparsers.add_parser('rnnoise'), int, True, False)
    # eq
    # change status
    parser_generic(subparsers.add_parser('reconnect'), int, True, False)
    parser_generic(subparsers.add_parser('change_hd'), str, False, True)
    parser_generic(subparsers.add_parser('volume'), str, True, True)
    parser_generic(subparsers.add_parser('app-volume'), int, False, False)
    # move app device
    # get stream volume
    # get config
    # save config

    args = parser.parse_args()
    
    arg_interpreter(args, parser, c)


def arg_interpreter(args, parser, client):
    #if len(args) <= 1 or loglevel > 0:
        #return

    # ----------------
    # Format devices
    # ----------------    
    # connect is the only command which uses 2 devices
    # TODO: Maybe find a more elegant solution
    if args.command == 'connect':
        if args.hardware_input: input_device=f'hi {args.hardware_input}'
        elif args.virtual_input: input_device=f'vi {args.virtual_input}'
        elif args.a: output_device=f'a {args.a}'
        elif args.b: output_device=f'b {args.b}'
        else:
            parser.error('device is unknown. (unknown device coming from parser)')
    else:
        if args.hardware_input: device=f'hi {args.hardware_input}'
        elif args.virtual_input: device=f'vi {args.virtual_input}'
        elif args.a: device=f'a {args.a}'
        elif args.b: device=f'b {args.b}'
        else:
            parser.error('device is unknown. (unknown device coming from parser)')

    # ----------------

    if args.command == 'connect':
        if args.value == None:
            client.send_command(f'{input_device} {output_device}')
        else:
            client.send_command(f'{input_device} {output_device} {args.value}')

    elif args.command == 'mute':
        if args.value != None:
            bool_value = str_to_bool(args.value, parser)
            if type(bool_value) == bool:
                client.send_command(f'mute {device} {bool_value}')
            else:
                parser.error('value has to be [true|false], [1|0] or [on|off]')
        else:
            client.send_command(f'mute {device}')

    elif args.command == 'rnnoise':
        client.send_command(f'rnnoise {args.value}')    

    elif args.command == 'reconnect':
        client.send_command(f'reconnect {device}')

    elif args.command == 'change_hd':
        client.send_command(f'change_hd {device} {args.value}')
    
    # TODO: add regex
    elif args.command == 'volume':
        if args.value != None:
            if args.value[0] in ['+', '-'] and args.value[1:].isnumeric():
                client.send_command(f'volume {device} {args.value}')
            elif args.value.isnumeric():
                client.send_command(f'volume {device} {args.value}')
            else:
                parser.error('Unknown prefix in value.\nPlease only use "+[number] or "-[number]" as a prefix.')
        else:
            parser.error('the following arguments are required: value')

    elif args.command == 'app-volume':
        client.send_command(f'app-volume {value}')

    sys.exit(0)

def main():
    loglevel = 0
    if 'loglevel-all' in sys.argv:
        loglevel = 2
    if 'loglevel-error' in sys.argv:
        loglevel = 1
        
    pulse = Pulse(loglevel=loglevel)

    if len(sys.argv) == 1:
        print('no argument given')
    elif sys.argv[1] == 'server':
        Server(pulse)
    elif sys.argv[1] == 'listen':
        c = Client()
        c.listen()
    elif sys.argv[1] == 'client':
        c = Client()
        while True:
            command = input()
            c.send_command(command)
            print(command)
            if len(command) == 0: break
    else:
        c = Client()
        while True:
            create_parser_args(c)
            if len(sys.argv[1]) == 0: break
    

    # else:
        # is_running()

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
