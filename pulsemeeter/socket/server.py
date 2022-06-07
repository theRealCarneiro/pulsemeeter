import socket
import re
import json
import sys
import os
import signal
import threading
import codecs
import traceback
import time
from queue import SimpleQueue

from ..backends import AudioServer, PulseSocket
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

        self.config_changes_thread = None
        self.config = self.read_config()
        # saves the timestamp of the last config change to check how long ago the last change was
        self.last_config_change = 0

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

        self.pulse_socket = PulseSocket(self.command_queue, self.config)
        self.audio_server = AudioServer(self.pulse_socket, self.config, loglevel=0, init=init_audio_server)

        self.create_command_dict()

    def start_server(self, daemon=False):

        self.main_loop_thread = threading.Thread(target=self.main_loop)
        self.main_loop_thread.start()

        # Start listener thread
        self.listener_thread = threading.Thread(target=self.query_clients)
        self.listener_thread.start()

        # start listening for Pulseaudio/Pipewire events
        self.pulse_socket.start_listener()

        # Thread for saving the config changes
        # collects all changes and writes them together
        self.stop_changes_thread = False
        # self.config_changes_thread = threading.Thread(target=self._wait_for_config_changes)

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
                print('[ERROR] Could not close client listener')
                traceback.print_exc()

            try:
                self.pulse_socket.stop_listener()
            except:
                print('[ERROR] Could not close pulse listener')
                traceback.print_exc()

            # Call any code to clean up virtual devices or similar
            self.close_server()

    def to_bytes(self, s):
        if type(s) is bytes:
            return s
        elif type(s) is str:
            return codecs.encode(s, 'utf-8')
        else:
            raise TypeError(f"[ERROR] [function: to_bytes()@{__name__}] Expected bytes or string, but got {type(s)}.")

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

    # function to register as a signal handler to gracefully exit
    def handle_exit_signal(self, signum=None, frame=None):
        self.command_queue.put(('exit',))

    # TODO: if the daemon should clean up its virtual devices on exit, do that here
    def close_server(self):
        # self.audio_server
        self.save_config(buffer=False)
        if self.config['cleanup']:
            self.audio_server.cleanup()
        self.closed = True

    # handles connection requests
    def query_clients(self):
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

    # get data stream and pass it into command handling function
    def listen_to_client(self, conn, event_queue, id):
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

    # handles incoming commands
    def handle_command(self, data):
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
            save_to_config = self.commands[command]['save_config']
            ret_msg = function(*args)

            if not ret_msg:
                raise Exception('[ERROR] internal error')

            if save_to_config:
                self.save_config()

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

    # change buffer to not wait for other changes
    def save_config(self, config=None, buffer=True):
        # the buffer is there to wait for all other changes in a time of 20 secs to be made and then write them all together
        if buffer is True:
            self.last_config_change = time.time()
            if self.config_changes_thread is not None and \
                    self.config_changes_thread.is_alive() is False:
                self.config_changes_thread.start()
        else:
            # gracefully exit the thread
            self._stop_config_changes_thread()
            if self.config_changes_thread is not None and \
                    self.config_changes_thread.is_alive():
                self.config_changes_thread.join()
            self._write_config(config)

    # handles writing the config to the file
    def _write_config(self, config=None):
        # interupt the changes thread because config gets saved now anyways
        # it also checks if the config_changes_thread is not saving the config (so it does not join itself)
        if (self.config_changes_thread is not None and
                self.config_changes_thread.is_alive() and
                threading.current_thread() != self.config_changes_thread):
            self.config_changes_thread.join()
        # save the config
        if config is None: config = self.config
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        print("writing config")
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(config, outfile, indent='\t', separators=(',', ': '))

    # This function is used to save the config when there were no changes for the set amount of time
    # This is useful for optimizing the performance and disk usage
    def _wait_for_config_changes(self):
        while True:
            if self.stop_changes_thread is True:
                self.stop_changes_thread = False
                break
            # check if the last config change is over 15 secs ago
            if (time.time() - self.last_config_change) > 15:
                self._write_config()
                break
            # this sleep just generally improves performance as we don't need very accurate time
            # if not done the thread will use 100% performance
            time.sleep(1)

    # this just lets the config changes thread decide if it should stop
    def _stop_config_changes_thread(self):
        self.stop_changes_thread = True

    def set_tray(self, state):
        if type(state) == str:
            state = state.lower() == 'true'
        self.config['tray'] = state
        ret_msg = f'tray {state}'
        return ret_msg

    def change_layout(self, layout):
        self.config['layout'] = layout
        return f'layout {layout}'

    def set_cleanup(self, state):
        state = str2bool(state)
        self.config['cleanup'] = state
        ret = f'cleanup {state}'
        return ret

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
                'save_config': True,
                'regex': f'(vi|hi) [0-9]+( (a|b) [0-9]+)?( ({state}))?( [0-9]+)?$'
            },

            # ARGS: [hi|vi|a|b] [None|STATE]
            # None = toggle
            'mute': {
                'function': self.audio_server.mute,
                'notify': True,
                'save_config': True,
                'regex': f'(vi|hi|a|b) [0-9]+( ({state}))?$'
            },

            # ARGS: [hi|vi|a|b]
            'primary': {
                'function': self.audio_server.set_primary,
                'notify': True,
                'save_config': True,
                'regex': r'(vi|hi|a|b) [0-9]+$'
            },

            # ARGS: id
            # id = hardware input id
            'rnnoise': {
                'function': self.audio_server.rnnoise,
                'notify': True,
                'save_config': True,
                'regex': f'[0-9]+( ({state}|(set [0-9]+ [0-9]+)))?$'
            },

            # ARGS: [a|b] id [None|STATE|set] [None|control]
            # 'set' is for saving a new control value, if used you HAVE to pass
            # control, you can ommit the second and third args to toggle
            'eq': {
                'function': self.audio_server.eq,
                'notify': True,
                'save_config': True,
                'regex': r'(a|b) [0-9]+( ((True|False|1|0|on|off|true|false)|(set ([0-9]+(\.[0-9]+)?)(,[0-9]+(\.[0-9]+)?){{14}})))?$'
            },

            ''
            # ARGS: [hi|a] id STATE
            # this will cleanup a hardware device and will not affect the config
            # useful when e.g. changing the device used in a hardware input strip
            'toggle-hd': {
                'function': self.audio_server.toggle_hardware_device,
                'notify': False,
                'save_config': False,
                'regex': f'(hi|a) [0-9]+( {state})?$'
            },

            # ARGS: [vi|b] id STATE
            # this will cleanup a virtual device and will not affect the config
            # useful when e.g. renaming the device
            'toggle-vd': {
                'function': self.audio_server.toggle_virtual_device,
                'notify': False,
                'save_config': False,
                'regex': f'(vi|b) [0-9]+( {state})?$'
            },

            # ARGS: [a|b|vi|hi] id NEW_NAME
            'rename': {
                'function': self.audio_server.rename,
                'notify': True,
                'regex': ''
            },

            # ARGS: [a|hi] id NEW_DEVICE
            # NEW_DEVICE is the name of the device
            'change_hd': {
                'function': self.audio_server.change_hardware_device,
                'notify': True,
                'save_config': True,
                'regex': r'(a|hi) [0-9]+ \w([\w\.-]+)?$'
            },

            # ARGS: [hi|vi|a|b] id vol
            # vol can be an absolute number from 0 to 153
            # you can also add and subtract
            'volume': {
                'function': self.audio_server.volume,
                'notify': True,
                'save_config': True,
                'regex': '(a|b|hi|vi) [0-9]+ [+-]?[0-9]+$'
            },

            # ARGS: id vol [sink-input|source-output]
            # vol can ONLY be an absolute number from 0 to 153
            'app-volume': {
                'function': self.audio_server.app_volume,
                'notify': True,
                'save_config': False,
                'regex': '[0-9]+ [0-9]+ (sink-input|source-output)$'
            },

            # ARGS: id device [sink-input|source-output]
            'move-app-device': {
                'function': self.audio_server.move_app_device,
                'notify': True,
                'save_config': False,
                'regex': r'[0-9]+ \w([\w\.-]+)? (sink-input|source-output)$'
            },

            'port-map': {
                'function': self.audio_server.set_port_map,
                'notify': True,
                'save_config': False,
                'regex': '(vi|hi) [0-9]+ (a|b)[0-9]+'
            },

            'auto-ports': {
                'function': self.audio_server.set_auto_ports,
                'notify': True,
                'save_config': False,
                'regex': f'(vi|hi) [0-9]+ (a|b)[0-9]+ {state}'
            },

            'get-config': {
                'function': self.get_config,
                'notify': False,
                'save_config': False,
                'regex': ''
            },

            'save_config': {
                'function': self.save_config,
                'notify': False,
                # already saves the config without the waiting
                'save_config': False,
                'regex': ''
            },

            'set-cleanup': {
                'function': self.set_cleanup,
                'notify': True,
                'save_config': False,
                'regex': f'{state}$'
            },

            'set-layout': {
                'function': self.change_layout,
                'notify': True,
                'regex': '[aA-zZ]+$'
            },

            'set-tray': {
                'function': self.set_tray,
                'notify': True,
                'save_config': True,
                'regex': f'{state}$'
            },

            'device-new': {
                'function': self.audio_server.device_new,
                'notify': True,
                'save_config': False,
                'regex': ''
            },

            'device-remove': {
                'function': self.audio_server.device_remove,
                'notify': True,
                'save_config': False,
                'regex': ''
            },
        }


def str2bool(v):
    if type(v) == bool:
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
