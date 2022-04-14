import socket
import re
import json
import sys
import os
import signal
import threading
import codecs
import traceback
from queue import SimpleQueue

import asyncio

from ..backends import Pulse
from ..settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, SOCK_FILE, __version__, PIDFILE


LISTENER_TIMEOUT = 2

class Server:
    def __init__(self, init_audio_server=True):

        # delete socket file if exists
        try:
            if self.is_running():
                raise ConnectionAbortedError('Another copy is already running')
            os.unlink(SOCK_FILE)
        except OSError:
            if os.path.exists(SOCK_FILE):
                raise


        # audio server can be pulse or pipe, so just use a generic name
        self.closed = False
        audio_server = Pulse

        self.config = self.read_config()
        self.audio_server = audio_server(self.config, loglevel=0, init=init_audio_server)
        self.create_command_dict()


        # the socket only needs to be seen by the listener thread
        # self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        #    # list of messages to deliver to listening clients
        #    self.msg_queue = []
        #
        #    # list of clients
        #    self.client_list = []
        #    self.client_command_thread_list = []

        self.exit_flag = False
        self.command_queue = SimpleQueue()
        self.client_exit_queue = SimpleQueue()
        self.event_queues = {}
        self.client_handler_threads = {}
        self.client_handler_connections = {}

    def start_server(self, daemon=False):

        # the asyncio loop
        self.async_loop = asyncio.get_event_loop()

        # Start listener thread
        self.listener_thread = threading.Thread(target=self.query_clients)
        self.listener_thread.start()

        self.main_loop_thread = threading.Thread(target=self.main_loop)
        self.main_loop_thread.start()

        # add the async task to listen to pulseaudio events
        self.pulse_listener_task = asyncio.run_coroutine_threadsafe(self.pulse_listener(), self.async_loop)

        # run the async code in thread
        self.pulse_listener_thread = threading.Thread(target=self.async_loop.run_forever, daemon=True)
        self.pulse_listener_thread.start()
        
        # Register signal handlers
        if daemon:
            signal.signal(signal.SIGINT, self.handle_exit_signal)
            signal.signal(signal.SIGTERM, self.handle_exit_signal)

        # self.notify_thread = threading.Thread(target=self.event_notify)
        # self.notify_thread.start()
    
    
    def main_loop(self):
        # Make sure that even in the event of an error, cleanup still happens
        try:
            # Listen for commands
            while True:
                message = self.command_queue.get()
                # if the message is None, exit. Otherwise, pass it to handle_command().
                # The string matching could probably be replaced with an enum if it's too slow
                # if message[0] == 'exit':
                    # break
                if message[0] == 'client_handler_exit':
                    if message[1] in self.event_queues:
                        del self.event_queues[message[1]]
                    del self.client_handler_connections[message[1]]
                    self.client_handler_threads.pop(message[1]).join()

                elif message[0] in ['command', 'exit', 'audio_server']:

                    if message[0] == 'command':
                        ret_message, notify_all = self.handle_command(message[2])
                        sender_id = message[1]
                    else:
                        ret_message = message[0] if message[0] == 'exit' else message[2]
                        notify_all = True
                        sender_id = None

                    # print(ret_message)
                    if ret_message:
                        self.send_message(ret_message, message, sender_id, notify_all)

                    if ret_message == 'exit':
                        break

            # TODO: maybe here would be the spot to sent an event signifying that the daemon is shutting down
            # TODO: if we do that, have those client handlers close by themselves instead of shutting down their connections
            # And maybe wait a bit for that to happen
            # Close connections and join threads
            print('closing client handler threads...')
            for conn in self.client_handler_connections.values():
                # only close open connections
                if conn.fileno() != -1:
                    conn.shutdown(socket.SHUT_RDWR)
            
            # Not sure if joining the client handler threads is actually necessary since we're stopping anyway and the
            # client handler threads are in daemon mode
            for thread in self.client_handler_threads.values():
                thread.join()

        finally:
            # Set the exit flag and wait for the listener thread to timeout
            print(f'sending exit signal to listener threads, they should exit within {LISTENER_TIMEOUT} seconds...')
            self.exit_flag = True
            try:
                self.listener_thread.join()
            except:
                print('Could not exit client listener')
            
            try:
                self.pulse_listener_task.cancel()                    
                self.async_loop.stop()
                self.pulse_listener_thread.join()
            except:
                print('could not exit pulse listener')


            # Call any code to clean up virtual devices or similar
            self.close_server()
    
    def to_bytes(self, s):
        if type(s) is bytes:
            return s
        elif type(s) is str or (sys.version_info[0] < 3 and type(s) is unicode):
            return codecs.encode(s, 'utf-8')
        else:
            raise TypeError("Expected bytes or string, but got %s." % type(s))
    
    def send_message(self, ret_message, message, sender_id, notify_all):
        encoded_msg = self.to_bytes(ret_message)
        # encoded_msg = ret_message.encode()

        # notify observers
        client_list = []
        if notify_all:
            client_list = self.client_handler_connections.values()
        elif sender_id in self.client_handler_connections:
            client_list = [self.client_handler_connections[message[1]]]
        # else:
            # continue

        for conn in client_list:

            # add 0 until 4 characters long
            sender_id = str(sender_id).rjust(4, '0')
            msg_len = str(len(encoded_msg)).rjust(4, '0')

            # send to clients
            try:
                conn.sendall(sender_id.encode())  # sender id
                conn.sendall(msg_len.encode())  # message len
                conn.sendall(encoded_msg)  # command
            except OSError:
                print(f'client {sender_id} already disconnected, message not sent')
    
    def config_device_from_name(self, name):
        '''
        searches for device with name(pulseaudio device) and returns tuple:
        - device_type
        - device_id
        '''
        for device_type in ['a', 'b', 'hi', 'vi']:
            # iterate through all devices (can scale with device count)
            device_id_range = range(1, len(self.config[device_type])+1)
            for device_id in device_id_range:
                device_id = str(device_id)
                device_config = self.config[device_type][device_id]
                if device_config["name"] == name:
                    return {
                            "device_type": device_type, 
                            "device_id": device_id
                            }
        return
    
    # thanks EnumValue
    def fa_enum_to_string(self, argument):
        '''facility EnumValue to native string'''
        case = {
            'client',
            'sink_input',
            'source_output',
            'module',
            'sink',
            'source'
        }
        for case in case:
            if argument == case: return case

    async def pulse_listener_handler(self, event):
        '''
        handles incoming events from the pulseaudio listener
        (updates config if needed and alerts clients)
        '''
        if event.t == 'change':
            device = await self.audio_server.device_from_event(event)
            if device is not None:
                pulsem_device = self.config_device_from_name(device.name) 
                if pulsem_device is not None:
                    device_config = self.config[pulsem_device["device_type"]][pulsem_device["device_id"]]
                    # read the volume data from config and from pulseaudio
                    config_volume = device_config["vol"]
                    device_volume = int(round(device.volume.value_flat * 100))

                    # compare config value with pulseaudio value
                    if config_volume != device_volume:
                        command = f'volume {pulsem_device["device_type"]} {pulsem_device["device_id"]} {device_volume}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["vol"] = device_volume
                        return
                    
                    config_mute = device_config["mute"]
                    device_mute = bool(device.mute)

                    if config_mute != device_mute:
                        command = f'mute {pulsem_device["device_type"]} {pulsem_device["device_id"]} {device_mute}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["mute"] = device_mute
                        return
                    #TODO: Maybe add detection for connection changes

        elif event.t in ['new', 'remove']:
            index = event.index
            facility = self.fa_enum_to_string(event.facility)
            if event.t == 'new':
                command = f'device-new {index} {facility}'
            elif event.t == 'remove':
                command = f'device-remove {index} {facility}'
            self.command_queue.put(('audio_server', None, command))
    
    async def pulse_listener(self):
        '''listener for pulseaudio events'''
        async with self.audio_server.pulsectl_async as pulse:
            async for event in pulse.subscribe_events('all'):
                await self.pulse_listener_handler(event)

    def is_running(self):
        try:
            with open(PIDFILE) as f:
                pid = int(next(f))

            # if pid of running instance
            if os.kill(pid, 0) is not False:
                return True
            
            # if pid is of a closed instance
            else:
                # write pid to file
                with open(PIDFILE, 'w') as f:
                    f.write(f'{os.getpid()}\n')
                return False

        # PIDFILE does not exist
        except Exception:
            with open(PIDFILE, 'w') as f:
                f.write(f'{os.getpid()}\n')
            return False


    def handle_exit_signal(self, signum=None, frame=None):
        '''function to register as a signal handler to gracefully exit'''
        self.command_queue.put(('exit',))

    # TODO: if the daemon should clean up its virtual devices on exit, do that here
    def close_server(self):
        # self.audio_server
        self.save_config()
        if self.config['cleanup']:
            self.audio_server.cleanup()
        self.closed = True

    def query_clients(self):
        '''handles connection requests'''
        # loop to get new connections
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(LISTENER_TIMEOUT)
            s.bind(SOCK_FILE)
            s.listen()
            id = 0
            while True:
                try:
                    # Wait for a connection
                    conn, addr = s.accept()
                    # print('client connected ', id)

                    # send id to client
                    conn.sendall(str.encode(str(id).rjust(4, '0')))

                    # Create a thread for the client
                    event_queue = SimpleQueue()
                    self.client_handler_connections[id] = conn
                    self.event_queues[id] = event_queue
                    thread = threading.Thread(target=self.listen_to_client, 
                            args=(conn, event_queue, id), daemon=True)
                    thread.start()
                    self.client_handler_threads[id] = thread
                    id += 1

                    # Check for an exit flag
                    if self.exit_flag:
                        break
                except socket.timeout:
                    if self.exit_flag:
                        break

    def listen_to_client(self, conn, event_queue, id):
        '''get data stream and pass it into command handling function'''
        with conn:
            while True:
                try:
                    # TODO: rework to include the length as the first 4 bytes. Get the daemon working first though, then
                    # TODO: work on compatibility.
                    msg_len = conn.recv(4)
                    if not len:
                        raise
                    msg_len = int(msg_len.decode())

                    data = conn.recv(msg_len)
                    if not data: raise

                    self.command_queue.put(('command', id, data))
                    # TODO: If this handler is being used for sending events to clients, distinguish a return value from
                    # TODO: an event
                except Exception:  # Exception doesn't catch exit exceptions (a bare except clause does)
                    # print(f'client {id} disconnect')
                    conn.shutdown(socket.SHUT_RDWR)
                    # Notify the main process that this client handler is closing, so it can free its resources
                    self.command_queue.put(('client_handler_exit', id))
                    self.client_exit_queue.put(id)
                    break

    
    def handle_command(self, data):
        '''handles incoming commands'''
        decoded_data = data.decode()
        msg = tuple(decoded_data.split(' '))
        str_args = re.sub(r'^.*?\ ', '', decoded_data)
        command = msg[0]
        if len(msg) > 1:
            args = msg[1:]
        else:
            args = ()

        # print(command, args)

        if command == 'exit':
            return command, True

        try:
            # verify that command existes
            if command not in self.commands:
                raise Exception(f'[ERROR] command \'{command}\' not found')

            if not re.match(self.commands[command]['regex'], str_args):
                raise Exception('[ERROR] invalid arguments')

            function = self.commands[command]['function']
            notify = self.commands[command]['notify']
            ret_msg = function(*args)

            if not ret_msg:
                raise Exception('[ERROR] internal error')

            return (ret_msg, notify,)

        except TypeError:
            return ('[ERROR] invalid number of arguments', False)

        except Exception as ex:
            return (str(ex), False)

    def read_config(self):
        # if config exists XDG_CONFIG_HOME
        if os.path.isfile(CONFIG_FILE):
            try:
                config = json.load(open(CONFIG_FILE))
            except Exception:
                print('[ERROR] loading config file')
                sys.exit(1)

            # if config is outdated it will try to add missing keys
            if 'version' not in config or config['version'] != __version__:
                config_orig = json.load(open(ORIG_CONFIG_FILE))
                config['version'] = __version__

                for key in config_orig:
                    if key not in config:
                        config[key] = config_orig[key]

                for i in ['a', 'b', 'vi', 'hi']:
                    for j in config_orig[i]:
                        for k in config_orig[i][j]:
                            if k not in config[i][j]:
                                config[i][j][k] = config_orig[i][j][k]
                self.save_config(config)
        else:
            config = json.load(open(ORIG_CONFIG_FILE))
            config['version'] = __version__
            self.save_config(config)

        return config

    def get_config(self, args=None):
        if args is None:
            return json.dumps(self.config, ensure_ascii=False)
        else:
            args = args.split(':')
            # print(args)
            config = self.config
            for arg in args:
                config = config[arg]

            if type(config) != dict:
                return config
            else:
                return json.dumps(config, ensure_ascii=False)


    def save_config(self, config=None):
        if config is None: config = self.config
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(config, outfile, indent='\t', separators=(',', ': '))

    def set_tray(self, state):
        if type(state) == str:
            state = state.lower() == 'true'
        self.config['tray'] = state
        ret_msg = f'tray {state}'
        return ret_msg

    def create_command_dict(self):

        # some useful regex
        state = '(True|False|1|0|on|off|true|false)'
        # eq_control = r'([0-9](\.[0-9])?)(,[0-9](\.[0-9])?){14}'

        # None means that is an optional argument
        # STATE == [ [connect|true|on|1] | [disconnect|false|off|0] ]
        self.commands = {
            # ARGS: [hi|vi] id [a|b] id [None|STATE]
            # None = toggle
            'connect': {
                'function': self.audio_server.connect,
                'notify': True,
                'regex': f'(vi|hi) [0-9]+( (a|b) [0-9]+)?( ({state}))?( [0-9]+)?$'
            },

            # ARGS: [hi|vi|a|b] [None|STATE]
            # None = toggle
            'mute': {
                'function': self.audio_server.mute,
                'notify': True,
                'regex': f'(vi|hi|a|b) [0-9]+( ({state}))?$'
            },

            # ARGS: [hi|vi|a|b]
            'primary': {
                'function': self.audio_server.set_primary,
                'notify': True,
                'regex': r'(vi|hi|a|b) [0-9]+$'
            },

            # ARGS: id
            # id = hardware input id
            'rnnoise': {
                'function': self.audio_server.rnnoise,
                'notify': True,
                'regex': f'[0-9]+( ({state}|(set [0-9]+ [0-9]+)))?$'
            },

            # ARGS: [a|b] id [None|STATE|set] [None|control]
            # 'set' is for saving a new control value, if used you HAVE to pass
            # control, you can ommit the second and third args to toggle
            'eq': {
                'function': self.audio_server.eq,
                'notify': True,
                'regex': r'(a|b) [0-9]+( ((True|False|1|0|on|off|true|false)|(set ([0-9]+(\.[0-9]+)?)(,[0-9]+(\.[0-9]+)?){{14}})))?$'
            },

            ''
            # ARGS: [hi|a] id STATE
            # this will cleanup a hardware device and will not affect the config
            # useful when e.g. changing the device used in a hardware input strip
            'toggle-hd': {
                'function': self.audio_server.toggle_hardware_device,
                'notify': False,
                'regex': f'(hi|a) [0-9]+( {state})?$'
            },

            # ARGS: [vi|b] id STATE
            # this will cleanup a virtual device and will not affect the config
            # useful when e.g. renaming the device
            'toggle-vd': {
                'function': self.audio_server.toggle_virtual_device,
                'notify': False,
                'regex': f'(vi|b) [0-9]+( {state})?$'
            },

            # ARGS: [hi|vi] id
            # wont affect config
            # 'reconnect': {
            # 'function': self.audio_server.reconnect,
            # 'notify': False,
            # 'regex': ''
            # },


            # ARGS: [a|hi] id NEW_DEVICE
            # NEW_DEVICE is the name of the device
            'change_hd': {
                'function': self.audio_server.change_hardware_device,
                'notify': True,
                'regex': r'(a|hi) [0-9]+ \w([\w\.-]+)?$'
            },

            # ARGS: [hi|vi|a|b] id vol
            # vol can be an absolute number from 0 to 153
            # you can also add and subtract
            'volume': {
                'function': self.audio_server.volume,
                'notify': True,
                'regex': '(a|b|hi|vi) [0-9]+ [+-]?[0-9]+$'
            },

            # ARGS: id vol [sink-input|source-output]
            # vol can ONLY be an absolute number from 0 to 153
            'app-volume': {
                'function': self.audio_server.app_volume,
                'notify': True,
                'regex': '[0-9]+ [0-9]+ (sink-input|source-output)$'
            },

            # ARGS: id device [sink-input|source-output]
            'move-app-device': {
                'function': self.audio_server.move_app_device,
                'notify': True,
                'regex': r'[0-9]+ \w([\w\.-]+)? (sink-input|source-output)$'
            },

            # ARGS: id [sink-input|source-output]
            'get-stream-volume': {
                'function': self.audio_server.get_app_stream_volume,
                'notify': False,
                'regex': '[0-9]+ (sink-input|source-output)$'
            },

            # ARGS: [sink-input|source-output]
            'get-app-list': {
                'function': self.audio_server.get_app_streams,
                'notify': False,
                'regex': '(sink-input|source-output)$'
            },

            'get-config': {
                'function': self.get_config,
                'notify': False,
                'regex': ''
            },

            'save_config': {
                'function': self.save_config,
                'notify': False,
                'regex': ''
            },

            'set-layout': {
                'function': self.audio_server.change_layout,
                'notify': True,
                'regex': '[aA-zZ]+$'
            },

            'set-cleanup': {
                'function': self.audio_server.set_cleanup,
                'notify': True,
                'regex': f'{state}$'
            },

            'set-tray': {
                'function': self.set_tray,
                'notify': True,
                'regex': f'{state}$'
            },

            'device-new': {
                'function': self.audio_server.device_new,
                'notify': True,
                'regex': ''
            },

            'device-remove': {
                'function': self.audio_server.device_remove,
                'notify': True,
                'regex': ''
            },

            # not ready
            'get-vd': {
                'function': self.audio_server.get_virtual_devices,
                'notify': False,
                'regex': ''
            },
            'get-hd': {
                'function':
                self.audio_server.get_hardware_devices,
                'notify': False,
                'regex': ''
            },
            'list-apps': {
                'function': self.audio_server.get_virtual_devices,
                'notify': False,
                'regex': ''
            },
            'rename': {
                'function': self.audio_server.rename,
                'notify': True,
                'regex': ''
            },

        }
