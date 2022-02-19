import os
import signal
import json
import sys, threading
import argparse
import re
import textwrap

from .settings import PIDFILE
from . import MainWindow
from . import Pulse
from . import Client, Server

from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')
from gi.repository import Gtk

# change these to change all occurences of these values (also for checking)
true_values = ('true', '1', 'on')
false_values = ('false', '0', 'off')

# change these to just change help text and other things where it just prints
input_values = ('hi', 'vi')
output_values = ('a', 'b')

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
        self.CLEAR = '\033[2J'
        self.END = '\033[0m'
        self.text = text

    def bold(self):
        return self.BOLD + self.text + self.END
    def red_bold(self):
        return self.BOLD_RED + self.text + self.END
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
            if command == 'listen' or 'Listen':
                server_listen_mode(client)
            elif command == 'exit' or 'Exit':
                raise KeyboardInterrupt
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

# PRETTY PRINT
def pprint_bool_options(style='simple'):
    # pretty print boolean values
    if style == 'pretty':
        return ' | '.join(map(str, true_values))+'\n'+' | '.join(map(str, false_values))
    elif style == 'simple':
        return '('+'|'.join(map(str, true_values))+') | ('+'|'.join(map(str, false_values))+')'

def pprint_device_options(devices='all'):
    # pretty print devices
    if devices == 'all':
        return '[number] | '.join((map(str, input_values)))+'[number] | '+'[number] | '.join(map(str, output_values))+'[number]'
    elif devices == 'input':
        return '[number] | '.join(map(str, input_values))+'[number]'
    elif devices == 'output':
        return '[number] | '.join(map(str, output_values))+'[number]'
    elif devices == None:
        pass

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
def convert_device(args, parser, device_type='general', allowed_devices=('hi', 'vi', 'a', 'b')):
    if device_type == 'general':
        # convert all devices
        try:
            # return device + value
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
def parser_generic(parser, value_type, help='', device_help='all'):
    parser.add_argument('device', **device_arg, help=pprint_device_options(device_help))
    if value_type is not None:
        parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# only value
def parser_only_value(parser, value_type, help=''):
    parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# source -> sink (only used for connect)
def parser_source_to_sink(parser, value_type, help='', help_input=pprint_device_options('input'), help_output=pprint_device_options('output')):
    parser.add_argument('input', **device_arg, help=help_input)
    parser.add_argument('output', **device_arg, help=help_output)
    parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# only device type + [value]
def parser_only_device(parser, value_type):
    parser.add_argument('device', **device_arg, help='hi | vi | a | b')
    if value_type is not None:
        parser.add_argument('value', type=value_type, default=None, nargs='?', help=help)

# only eq and rnnoise
def parser_eq_rnnoise(parser, type):
    if type == 'eq':
        parser.add_argument('device', **device_arg, help=pprint_device_options('output'))
        value_help = 'Only needed when using set as state. Needs 15 values seperated by with a comma.'
    elif type == 'rnnoise':
        parser.add_argument('device', **device_arg, help=pprint_device_options('input'))
        value_help = 'Only needed when using set as state.'
    parser.add_argument('state', type=str, choices=(*true_values, *false_values, 'set', None), default=None, nargs='?', help='')
    parser.add_argument('value', type=str, default=None, nargs='?', help=value_help)

# ARGS INTERPRETER AND PARSER
def create_parser_args():
    parser = argparse.ArgumentParser(prog='pulsemeeter', usage='%(prog)s', description=(f'Use "{format("%(prog)s [command] -h").green()}" to get usage information. Replicating voicemeeter routing functionalities in linux with pulseaudio.'))

    parser.add_argument('-d', '--debug', action='store_true', help='go into debug mode')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('daemon', description='start the daemon') # just to show it in the help menu
    parser_source_to_sink(subparsers.add_parser('connect', description='connect an input to an output.'), str, 'OPTIONAL '+pprint_bool_options())
    parser_generic(subparsers.add_parser('primary', description='Select primary device. Only available for virtual devices.'), None, '', None)
    parser_generic(subparsers.add_parser('mute', description='mute/unmute a device.'), str, 'OPTIONAL '+pprint_bool_options())
    parser_generic(subparsers.add_parser('change-hardware-device', description='change the hardware device'), str, 'name of the device')
    parser_generic(subparsers.add_parser('volume', description='change volume'), str, '+[value] | -[value] | [value]')
    parser_eq_rnnoise(subparsers.add_parser('rnnoise', usage = f'%(prog)s [device] [{pprint_bool_options()} | (set)] [value]', description='turn on/off noise reduction and change values. To toggle only include the device.'), 'rnnoise')
    parser_eq_rnnoise(subparsers.add_parser('eq', usage=f'%(prog)s [device] [{pprint_bool_options()} | (set)] [value1],[value2],[...]', description='turn on/off eq and change values. To toggle only include the device.'), 'eq')

    args = parser.parse_args()
    arg_interpreter(args, parser)

def arg_interpreter(args, parser):
    try:
        client = Client()
    except:
        print(format('error: daemon is not started. Use "pulsemeeter daemon" to start it').red_bold())
    else:
        if args.debug:
                print(f'You are entering the {format("debug mode").red()}.')
                print(f'While in INPUT mode type "{format("listen").bold()}" to switch to the LISTEN mode.')
                print(f'While in LISTEN mode use {format("ctrl+c").bold()} to switch back to INPUT mode.')
                debug_start(client, 'input')

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
            try:
                device = re.search(r'^(a|hi)+', args.device).group()
                num = re.search(r'\d+$', args.device).group()
                client.change_hardware_device(device, num, args.value)
            except:
                parser.error('device has to be assigned like this: [a|hi][number] [NEW_DEVICE].')

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
    try:
        server = Server()
        running = False
    except:
        running = True

    if len(sys.argv) == 1:
        if not running: server.start_server()
        app = MainWindow()
        Gtk.main()
        if not running: server.handle_exit_signal()

    elif sys.argv[1] == 'daemon':
        if running:
            print('Server is already running')
            sys.exit(1)
        server.start_server(daemon=True)
    else:
        create_parser_args()


if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
