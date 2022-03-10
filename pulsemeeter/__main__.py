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

all_get = ('volume', 'mute', 'primary', 'name', 'eq', 'rnnoise', 'connect')

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
        NO_COLOR = 'deactivate colors for the executed command'
        CONNECT = 'connect input to output'
        PRIMARY = 'select primary device'
        MUTE = 'mute/unmute a device'
        CHANGE_HARDWARE_DEVICE = 'Change the hardware device.'
        VOLUME = 'change volume'
        RNNOISE = 'Turn on/off noise reduction and change values. To toggle only include the device.'
        EQ = 'Turn on/off eq and change values. To toggle only include the device'
        RENAME = 'rename device'
        GET = 'eg. pulsemeeter get volume a1'

    class usage:
        RNNOISE = f'%(prog)s [device] ({pprint_bool_options()} | [set]) [value]'
        EQ = f'%(prog)s [device] ({pprint_bool_options()} | [set]) [value1],[value2],[...]'

    class value:
        MUTE = f'OPTIONAL {pprint_bool_options()}'
        CHANGE_HARDWARE_DEVICE = 'name of the device'
        VOLUME = '+[value] | -[value] | [value]'
        CONNECT = f'OPTIONAL {pprint_bool_options()}'
        PRIMARY = ''
        RENAME = 'name'
        GET = 'value to get'
        GET_DEVICE2 = 'only used for connect'

# COLORED TEXT
class format:
    # format text using ANSI escape codes
    def __init__(self, no_color=False):
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'
        self.GREEN = '\033[92m'
        self.RED = '\033[91m'
        self.YELLOW = '\033[33m'
        self.BOLD_RED = self.BOLD+self.RED
        self.GREY = '\033[30m'
        self.CLEAR = '\033[2J'
        self.END = '\033[0m'
        self.no_color = no_color

    def bold(self, text):
        if self.no_color: return text
        else: return self.BOLD + text + self.END
    def red_bold(self, text):
        if self.no_color: return text
        else: return self.BOLD_RED + text + self.END
    def grey(self, text):
        if self.no_color: return text
        else: return self.GREY + text + self.END
    def green(self, text):
        if self.no_color: return text
        else: return self.GREEN + text + self.END
    def yellow(self, text):
        if self.no_color: return text
        else: return self.YELLOW + text + self.END
    def red(self, text):
        if self.no_color: return text
        else: return self.RED + text + self.END
    # clear terminal
    def clear(self, text):
        if self.no_color: return text
        else: return self.CLEAR + self.END
    # print a color end
    def end(self, text):
        if self.no_color: return text
        else: return self.END


# DEBUG HELPERS
# start in specified mode and switch between them
def debug_start(client, start_option):
    if start_option == 'input':
        server_input_mode(client)
    elif start_option == 'listen':
        server_listen_mode(client)

def server_input_mode(client):
    print(f'\n{color.green("INPUT:")}')
    try:
        while client:
            command = input(color.bold('> '))
            if command.lower() == 'listen':
                server_listen_mode(client)
            elif command.lower() == 'exit':
                raise KeyboardInterrupt
            elif command == 'close server':
                print('closing server')
                client.close_server()
                raise KeyboardInterrupt
            else:
                print(client.send_command(command))
    except KeyboardInterrupt:
        print('closing debugger')
        sys.exit(0)

def server_listen_mode(client):
    print(f'\n{color.yellow("LISTEN:")}')
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
def convert_device(args, parser, device_type='general', allowed_devices=all_devices, con_in=None, con_out=None):
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
            if con_in is None and con_out is None:
                inputd = args.input
                outputd = args.output
            else: 
                inputd = con_in
                outputd = con_out
            in_device = re.match(r'^(hi|vi)', inputd).group()
            in_num = re.search(r'\d+$', inputd).group()
            out_device = re.match(r'^(a|b)', outputd).group()
            out_num = re.search(r'\d+$', outputd).group()
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

def parser_get(parser, type):
    parser.add_argument('value', type=type, help=help.value.GET, choices=all_get)
    parser.add_argument('device', **device_arg, help=pprint_device_options())
    parser.add_argument('device2', **device_arg, help=f'{pprint_device_options()} ({help.value.GET_DEVICE2})', default=None, nargs='?') 

# ARGS INTERPRETER AND PARSER
def create_parser_args():
    color = format()

    parser = argparse.ArgumentParser(prog='pulsemeeter', usage='%(prog)s', description=(f'Use "{color.green("%(prog)s [command] -h")}" to get usage information. Replicating voicemeeter routing functionalities in linux with pulseaudio.'))

    parser.add_argument('-nc', '--no-color', action='store_true', help=help.description.NO_COLOR)
    parser.add_argument('-d', '--debug', action='store_true', help=help.description.DEBUG)
    parser.add_argument('-s', '--status', action='store_true', help=help.description.STATUS)

    subparsers = parser.add_subparsers(dest='command')

    # commands to only show in help menu
    subparsers.add_parser('daemon')
    subparsers.add_parser('init')
    subparsers.add_parser('exit')

    # get (retrieve values)
    parser_get(subparsers.add_parser('get', description=help.description.GET), str)

    # source to sink (connect)
    parser_source_to_sink(subparsers.add_parser('connect', description=help.description.CONNECT), str, help.value.CONNECT)

    # generic (device and with value if not None)
    parser_generic(subparsers.add_parser('primary',description=help.description.PRIMARY), None, help.value.PRIMARY, ('vi', 'b'))
    parser_generic(subparsers.add_parser('mute', description=help.description.MUTE), str, help.value.MUTE)
    parser_generic(subparsers.add_parser('change-hardware-device', description=help.description.CHANGE_HARDWARE_DEVICE),str, help.value.CHANGE_HARDWARE_DEVICE, ('vi', 'b'))
    parser_generic(subparsers.add_parser('rename', description=help.description.RENAME), str, help.value.RENAME, ('vi', 'b'))
    parser_generic(subparsers.add_parser('volume', description=help.description.VOLUME), str, help.value.VOLUME)

    # eq or rnnoise (allows state)
    parser_eq_rnnoise(subparsers.add_parser('rnnoise', usage = help.usage.RNNOISE, description=help.description.RNNOISE), 'rnnoise')
    parser_eq_rnnoise(subparsers.add_parser('eq', usage=help.usage.EQ, description=help.description.EQ), 'eq')

    args = parser.parse_args()
    arg_interpreter(args, parser)

def arg_interpreter(args, parser):
    global color
    color = format(no_color=args.no_color)

    # commands which do not need a client
    if args.status:
        if another_sv_running:
            print(f'Server: {color.green("running")}')
        else:
            print(f'Server: {color.red("not running")}')

        try:
            subprocess.check_call('pmctl')
            print(f'Pulseaudio: {color.green("running")}')
        except:
            print(f'Pulseaudio: {color.red("not running")}')
        
        try:
            audio_server = os.popen('pactl info | grep "Server Name"').read()
            audio_server = audio_server.split(': ')[1]
            audio_server = audio_server.replace('\n', '')
        except:
            audio_server = color.red('could not be determined')
      
        print(f'audio server: {color.bold(audio_server)}')
        print(f'Pulsemeeter version: {color.bold(__version__)}')
        print(f'Config File: {color.bold(CONFIG_FILE)}')
        print(f'OS: {color.bold(platform.platform())}')
        print(f'Python version: {color.bold(sys.version)}')
        sys.exit(0)
    else:
        # commands which need a client
        try:
            client = Client()
        except:
            print(color.red('error: daemon is not started. Use "pulsemeeter daemon" to start it.'))
        else:
            # debug page
            if args.debug:
                    print(f'You are entering the {color.red("debug mode")}.')
                    print(f'While in INPUT mode type "{color.bold("listen")}" to switch to the LISTEN mode.')
                    print(f'While in LISTEN mode use {color.bold("ctrl+c")} to switch back to INPUT mode.')
                    debug_start(client, 'input')

            # COMMAND INTERPRETER

            # retrieve config values
            elif args.command == 'get':
                try:
                    if args.value == 'volume':
                        device_args = convert_device(args, parser)
                        print(client.config[device_args[0]][device_args[1]]['vol'])
                    elif args.value == 'mute':
                        device_args = convert_device(args, parser)
                        print(client.config[device_args[0]][device_args[1]]['mute'])
                    elif args.value == 'primary':
                        device_args = convert_device(args, parser, allowed_devices=('vi', 'b'))
                        print(client.config[device_args[0]][device_args[1]]['primary'])
                    elif args.value == 'name':
                        device_args = convert_device(args, parser, allowed_devices='vi')
                        print(client.config[device_args[0]][device_args[1]]['name'])
                    elif args.value == 'eq':
                        device_args = convert_device(args, parser, allowed_devices=('a', 'b'))
                        print(client.config[device_args[0]][device_args[1]]['use_eq'])
                    elif args.value == 'rnnoise':
                        device_args = convert_device(args, parser, allowed_devices='hi')
                        print(client.config[device_args[0]][device_args[1]]['use_rnnoise'])
                    elif args.value == 'connect':
                        device_args = convert_device(args, parser, 'source-to-sink', con_in=args.device, con_out=args.device2)
                        out = device_args[2]+device_args[3]
                        print(client.config[device_args[0]][device_args[1]][out])
                except:
                    print(color.red('error: Could not get value for this.'))

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
                client.primary(*convert_device(args, parser, allowed_devices=('vi', 'b')))

            elif args.command == 'change-hardware-device':
                client.change_hardware_device(*convert_device(args, parser, allowed_devices=('a', 'hi')), value)

            elif args.command == 'volume':
                device_args = convert_device(args, parser)
                if args.value is not None:
                    if re.match(r'[+|-]?\d+$', args.value):
                        client.volume(*(device_args), args.value)
                    else:
                        parser.error(f'value has to be assigned like this: {color.bold("+[number] | -[number] | [number]")}')
                else:
                    # do not blame me. I dont know how to insert the "" into the string
                    text = '"pulsemeeter get volume [device]"'
                    parser.error(f'the following arguments are required: value\n{color.grey("tip: To retrieve the volume use ")+color.grey(text)}')

            elif args.command == 'eq':
                client.eq(*convert_eq_rnnoise(args, parser, 'eq'))

            elif args.command == 'rnnoise':
                client.rnnoise(*convert_eq_rnnoise(args, parser, 'rnnoise'))

            elif args.command == 'rename':
                client.rename(*convert_device(args, parser), args.value)

    sys.exit(0)

def start_server(server):
    try:
        server.start_server(daemon=True)
        time.sleep(0.1)
    except:
        print('Could not start server')
        sys.exit(1)

def start_app(isserver, trayonly):
    app = MainWindow(isserver=isserver, trayonly=trayonly)
    Gtk.main()

def main():
    global another_sv_running

    try:
        server = Server()
        another_sv_running = False

    except ConnectionAbortedError:
        another_sv_running = True

    except Exception as ex:
        print(ex)
        return 1

    isserver = not another_sv_running

    #none: Start Server (if not already started) and open window 
    if len(sys.argv) == 1:
        trayonly = False

    # daemon: disable application window creation for instance
    elif sys.argv[1].lower() == 'daemon':
        if not isserver:
            print('The server is already running.')
            return 1
        
        trayonly = True

    # init: Just start devices and connections
    elif sys.argv[1] == 'init':
        return 0
    
    # exit: close server, all clients should close after they recive an exit signal from
    # the server
    elif sys.argv[1].lower() == 'exit':
        try:
            if another_sv_running:
                print('closing server...')
                print('It may take a few seconds...')
                client = Client()
                client.close_server()
                return 0
            else:
                print('no instance is running')
                return 1
        except Exception as ex:
            print('unable to close server', ex)
            return 1
    
    else:
        create_parser_args()
        return 0
    
    # only no args and daemon arg reach this part of the code
    if isserver: start_server(server)
    start_app(isserver, trayonly)
    if isserver: server.handle_exit_signal()

    return 0
