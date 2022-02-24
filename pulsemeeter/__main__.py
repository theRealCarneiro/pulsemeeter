import os
import time
import signal
import json
import sys, threading
import subprocess
import argparse
import re
import platform

from .settings import PIDFILE, CONFIG_FILE, __version__
from . import MainWindow
from . import Pulse
from . import Client, Server

from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')
from gi.repository import Gtk

# change these to change all occurences of these values (also for checking)
true_values = ('true', '1', 'on')
false_values = ('false', '0', 'off')

# change these to just change possible devices
all_devices = ('hi', 'vi', 'a', 'b')

# PRETTY PRINT
def pprint_bool_options(style='simple'):
    # pretty print boolean values
    if style == 'pretty':
        return ' | '.join(map(str, true_values))+'\n'+' | '.join(map(str, false_values))
    elif style == 'simple':
        return '['+'|'.join(map(str, true_values))+'] | ['+'|'.join(map(str, false_values))+']'

def pprint_device_options(allowed_devices = all_devices):
    # pretty print devices
    if type(allowed_devices) == str:
        return f'{allowed_devices}[number]'
    else:
        return f'{"[number] | ".join(map(str, allowed_devices))}[number]'

# HELP MESSAGES
class help:
    class description:
        DEBUG = 'go into debug mode'
        STATUS = 'status information'
        NO_COLOR = 'deactivate colors for this command'
        DAEMON = 'start the daemon'
        CONNECT = 'connect an input to an output'
        PRIMARY = 'Select primary device.'
        MUTE = 'mute/unmute a device'
        CHANGE_HARDWARE_DEVICE = 'Change the hardware device.'
        VOLUME = 'change volume'
        RNNOISE = 'Turn on/off noise reduction and change values. To toggle only include the device.'
        EQ = 'Turn on/off eq and change values. To toggle only include the device'

    class usage:
        RNNOISE = f'%(prog)s [device] ({pprint_bool_options()} | [set]) [value]'
        EQ = f'%(prog)s [device] ({pprint_bool_options()} | [set]) [value1],[value2],[...]'

    class value:
        MUTE = f'OPTIONAL {pprint_bool_options()}'
        CHANGE_HARDWARE_DEVICE = 'name of the device'
        VOLUME = '+[value] | -[value] | [value]'
        CONNECT = f'OPTIONAL {pprint_bool_options()}'
        PRIMARY = ''

# COLORED TEXT
class format:
    # format text using ANSI escape codes
    def __init__(self, text=''):
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'
        self.GREEN = '\033[92m'
        self.RED = '\033[91m'
        self.YELLOW = '\033[33m'
        self.BOLD_RED = self.BOLD+self.RED
        self.GREY = '\033[30m'
        self.CLEAR = '\033[2J'
        self.END = '\033[0m'
        self.text = text

    def bold(self):
        return self.BOLD + self.text + self.END
    def red_bold(self):
        return self.BOLD_RED + self.text + self.END
    def grey(self):
        return self.GREY + self.text + self.END
    def green(self):
        return self.GREEN + self.text + self.END
    def yellow(self):
        return self.YELLOW + self.text + self.END
    def red(self):
        return self.RED + self.text + self.END
    # clear terminal
    def clear(self):
        return self.CLEAR + self.END
    # print a color end
    def end(self):
        return self.END


# DEBUG HELPERS
# start in specified mode and switch between them
def debug_start(client, start_option):
    if start_option == 'input':
        server_input_mode(client)
    elif start_option == 'listen':
        server_listen_mode(client)

def server_input_mode(client):
    print(f'\n{format("INPUT:").green()}')
    try:
        while client:
            command = input(format('> ').bold())
            if command == 'listen':
                server_listen_mode(client)
            elif command == 'exit':
                raise KeyboardInterrupt
            elif command == 'close_server':
                client.send_command('exit')

            else:
                print(client.send_command(command))
    except KeyboardInterrupt:
        print('\nclosing debugger')
        sys.exit(0)

def server_listen_mode(client):
    print(f'\n{format("LISTEN:").yellow()}')
    try:
        client.listen()
    except KeyboardInterrupt:
        print()
        server_input_mode(client)

# CONVERTERS
def str_to_bool(string, parser):
    if type(string) == bool:
        return string
    elif string.lower() in true_values:
        return True
    elif string.lower() in false_values:
        return False
    else:
        parser.error(f'value has to be one of these options: {pprint_bool_options()}')

# check if values are valid and check devices for different type
def convert_eq_rnnoise(args, parser, type):
    # generate device_args by using sinks or sources
    if type == 'eq':
        device_args = convert_device(args, parser, 'general', ('a', 'b'))
    elif type == 'rnnoise':
        device_args = convert_device(args, parser, 'general', 'hi')
    # check if eq gets 15 values for control
    if args.state == 'set' and args.value is not None:
        if type == 'eq':
            values = args.value.split(',')
            if len(values) == 15:
                return (*device_args, args.state, args.value)
            else:
                parser.error('Wrong values supplied. You need to assign 15 values separated by a comma. (eg. 1,2,3,...)')
        elif type == 'rnnoise':
            return (device_args[1], args.state, args.value)
    else:
        if type == 'rnnoise':
            if args.state is None:
                return (device_args[1])
            else:
                return (*device_args[1], str_to_bool(args.state, parser))
        else:
            if args.state is None:
                return (device_args)
            else:
                return (*device_args, str_to_bool(args.state, parser))

# convert [device][number] -> [device] [number] and check if device is valid
def convert_device(args, parser, device_type='general', allowed_devices=all_devices):
    if device_type == 'general':
        # convert all devices
        try:
            # return device + value
            if type(allowed_devices) == str:
                device = re.match(f'^({allowed_devices})', args.device).group()
            else:
                device = re.match(f'^({"|".join(allowed_devices)})', args.device).group()
            num = re.search(r'\d+$', args.device).group()
        except:
            if type(allowed_devices) == str:
                parser.error(f'device has to be assigned like this: [{allowed_devices}][number].')
            else:
                parser.error(f'device has to be assigned like this: [{"|".join(allowed_devices)}][number].')
        else:
            return (device, num)
    elif device_type == 'source-to-sink':
        # convert source -> sink device
        try:
            in_device = re.match(r'^(hi|vi)', args.input).group()
            in_num = re.search(r'\d+$', args.input).group()
            out_device = re.match(r'^(a|b)', args.output).group()
            out_num = re.search(r'\d+$', args.output).group()
        except:
            parser.error('device has to be assigned like this: [hi|vi][number] [a|b][number]')
        else:
            return (in_device, in_num, out_device, out_num)
    else:
        parser.error(f'internal error: unknown device convert "{device_type}".')

# PARSER GENERATORS
device_arg = {'type': str}

# generic device = device + [value]
def parser_generic(parser, value_type, help='', device_help=all_devices):
    parser.add_argument('device', **device_arg, help=pprint_device_options(device_help))
    if value_type is not None:
        parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# source -> sink (only used for connect)
def parser_source_to_sink(parser, value_type, help='', help_input=pprint_device_options(('hi', 'vi')), help_output=pprint_device_options(('a', 'b'))):
    parser.add_argument('input', **device_arg, help=help_input)
    parser.add_argument('output', **device_arg, help=help_output)
    parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# only eq and rnnoise
def parser_eq_rnnoise(parser, type):
    if type == 'eq':
        parser.add_argument('device', **device_arg, help=pprint_device_options(('a', 'b')))
        value_help = 'Only needed when using set as state. Needs 15 values seperated by with a comma.'
    elif type == 'rnnoise':
        parser.add_argument('device', **device_arg, help=pprint_device_options('hi'))
        value_help = 'Only needed when using set as state.'
    parser.add_argument('state', type=str, choices=(*true_values, *false_values, 'set', None), default=None, nargs='?', help='')
    parser.add_argument('value', type=str, default=None, nargs='?', help=value_help)

# ARGS INTERPRETER AND PARSER
def create_parser_args():

    parser = argparse.ArgumentParser(prog='pulsemeeter', usage='%(prog)s', description=(f'Use "{format("%(prog)s [command] -h").green()}" to get usage information. Replicating voicemeeter routing functionalities in linux with pulseaudio.'))

    parser.add_argument('-d', '--debug', action='store_true', help=help.description.DEBUG)
    parser.add_argument('-s', '--status', action='store_true', help=help.description.STATUS)

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('daemon', description=help.description.DAEMON) # just to show it in the help menu
    parser_source_to_sink(subparsers.add_parser('connect', description=help.description.CONNECT), str, help.value.CONNECT)
    parser_generic(subparsers.add_parser('primary',description=help.description.PRIMARY), None, help.value.PRIMARY, ('vi', 'b'))
    parser_generic(subparsers.add_parser('mute', description=help.description.MUTE), str, help.value.MUTE)
    parser_generic(subparsers.add_parser('change-hardware-device', description=help.description.CHANGE_HARDWARE_DEVICE),str, help.value.CHANGE_HARDWARE_DEVICE, ('vi', 'b'))
    parser_generic(subparsers.add_parser('volume', description=help.description.VOLUME), str, help.value.VOLUME)
    parser_eq_rnnoise(subparsers.add_parser('rnnoise', usage = help.usage.RNNOISE, description=help.description.RNNOISE), 'rnnoise')
    parser_eq_rnnoise(subparsers.add_parser('eq', usage=help.usage.EQ, description=help.description.EQ), 'eq')

    args = parser.parse_args()
    arg_interpreter(args, parser)

def arg_interpreter(args, parser):
    if args.status:
        # information page
        if server_running:
            print(f'Server: {format("running").green()}')
        else:
            print(f'Server: {format("not running").red()}')

        try:
            subprocess.check_call('pmctl')
            print(f'Pulseaudio: {format("running").green()}')
        except:
            print(f'Pulseaudio: {format("not running").red()}')
        
        try:
            audio_server = os.popen('pactl info | grep "Server Name"').read()
            audio_server = audio_server.split(': ')[1]
            audio_server = audio_server.replace('\n', '')
            audio_server = format(audio_server).bold()
        except:
            audio_server = format('could not be determined').red()
      
        print(f'audio server: {audio_server}')
        print(f'Pulsemeeter version: {format(__version__).bold()}')
        print(f'Config File: {format(CONFIG_FILE).bold()}')
        print(f'OS: {format(platform.platform()).bold()}')
        print(f'Python version: {format(sys.version).bold()}')
        sys.exit(0)
    else:
        # try to connect with client
        try:
            client = Client()
        except:
            print(format('error: daemon is not started. Use "pulsemeeter daemon" to start it.').red())
        else:
            # debug page
            if args.debug:
                    print(f'You are entering the {format("debug mode").red()}.')
                    print(f'While in INPUT mode type "{format("listen").bold()}" to switch to the LISTEN mode.')
                    print(f'While in LISTEN mode use {format("ctrl+c").bold()} to switch back to INPUT mode.')
                    debug_start(client, 'input')

            # command interpreter
            elif args.command == 'connect':
                device_args = convert_device(args, parser, 'source-to-sink')
                if args.value is not None:
                    client.connect(*(device_args), str_to_bool(args.value, parser))
                else:
                    client.connect(*device_args)

            elif args.command == 'mute':
                device_args = convert_device(args, parser)
                if args.value is not None:
                    client.mute(*(device_args), str_to_bool(args.value, parser))
                else:
                    client.mute(*(device_args))

            elif args.command == 'primary':
                client.primary(*convert_device(args, parser, 'general', ('vi', 'b')))

            elif args.command == 'change-hardware-device':
                client.change_hardware_device(*convert_device(args, parser, 'generic', ('a', 'hi')), value)

            elif args.command == 'volume':
                device_args = convert_device(args, parser)
                if args.value is not None:
                    if re.match(r'[+|-]?\d+$', args.value):
                        client.volume(*(device_args), args.value)
                    else:
                        parser.error('value has to be assigned like this: +[number] | -[number] | [number]')
                else:
                    parser.error('the following arguments are required: value')

            elif args.command == 'eq':
                client.eq(*convert_eq_rnnoise(args, parser, 'eq'))

            elif args.command == 'rnnoise':
                client.rnnoise(*convert_eq_rnnoise(args, parser, 'rnnoise'))

    sys.exit(0)

def main():
    global server_running
    tray = None
    try:
        server = Server()
        server_running = False
        server.start_server(daemon=True)
        time.sleep(0.1)
    except:
        server_running = True
    isserver = not server_running

    if len(sys.argv) == 1:
        app = MainWindow(isserver=isserver, trayonly=False)
        Gtk.main()
        if isserver: 
            server.handle_exit_signal()

    elif sys.argv[1] == 'daemon':
        if not isserver:
            print('Server is already running')
            sys.exit(1)

        if server.config['tray']:
            app = MainWindow(isserver=True, trayonly=True)
            Gtk.main()
            server.handle_exit_signal()

    else:
        create_parser_args()
