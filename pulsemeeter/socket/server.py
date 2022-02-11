import socket
import json
import sys
import os
import signal
import threading
from queue import SimpleQueue

from ..backends import Pulse
from ..settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, SOCK_FILE, __version__


LISTENER_TIMEOUT = 1


class Server:
    def __init__(self):

        # audio server can be pulse or pipe, so just use a generic name
        audio_server = Pulse

        self.read_config()
        self.audio_server = audio_server(self.config)
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

        # delete socket file if exists
        try:
            os.unlink(SOCK_FILE)
        except OSError:
            if os.path.exists(SOCK_FILE):
                raise

        # Start listener thread
        self.listener_thread = threading.Thread(target=self.query_clients)
        self.listener_thread.start()

        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

        # self.notify_thread = threading.Thread(target=self.event_notify)
        # self.notify_thread.start()

        # Make sure that even in the event of an error, cleanup still happens
        try:
            # Listen for commands
            while True:
                message = self.command_queue.get()
                # if the message is None, exit. Otherwise, pass it to handle_command().
                # The string matching could probably be replaced with an enum if it's too slow
                if message[0] == 'exit':
                    break
                elif message[0] == 'client_handler_exit':
                    if message[1] in self.event_queues:
                        del self.event_queues[message[1]]
                    del self.client_handler_connections[message[1]]
                    self.client_handler_threads.pop(message[1]).join()
                elif message[0] == 'command':
                    # TODO: as mentioned in handle_command(), it probably needs a rework. This is for boilerplate.
                    ret_message, notify_all = self.handle_command(message[2])

                    if ret_message:
                        self.event_queues[message[1]].put(('return', ret_message, message[1]))
                        encoded_msg = ret_message.encode()

                        # notify observers
                        if notify_all:
                            client_list = self.client_handler_connections.values()
                        else:
                            client_list = [self.client_handler_connections[message[1]]]

                        for conn in client_list:
                            # add 0 until 4 characters long
                            id = str(message[1]).rjust(4, '0')
                            msg_len = str(len(encoded_msg)).rjust(4, '0')

                            # send to clients
                            try:
                                conn.sendall(id.encode()) # sender id
                                conn.sendall(msg_len.encode()) # message len
                                conn.sendall(encoded_msg) # command
                            except OSError:
                                print(f'client {message[1]} already disconnected, message not sent')
                                

            # TODO: maybe here would be the spot to sent an event signifying that the daemon is shutting down
            # TODO: if we do that, have those client handlers close by themselves instead of shutting down their connections
            # And maybe wait a bit for that to happen

            # Close connections and join threads
            print('closing client handler threads...')
            for conn in self.client_handler_connections.values():
                conn.shutdown(socket.SHUT_RDWR)

            # Not sure if joining the client handler threads is actually necessary since we're stopping anyway and the
            # client handler threads are in daemon mode
            for thread in self.client_handler_threads.values():
                thread.join()
        finally:
            # Set the exit flag and wait for the listener thread to timeout
            print(f'sending exit signal to listener thread, it should exit within {LISTENER_TIMEOUT} seconds...')
            self.exit_flag = True
            self.listener_thread.join()

            # Call any code to clean up virtual devices or similar
            self.close_server()

    def create_command_dict(self):
        ## None means that is an optional argument
        ## STATE == [ [connect|true|on|1] | [disconnect|false|off|0] ]
        self.commands = {
            # ARGS: [hi|vi] id [a|b] id [None|STATE]
            # None = toggle
            'connect': [self.audio_server.connect, True],

            # ARGS: [hi|vi|a|b] [None|STATE]
            # None = toggle
            'mute': [self.audio_server.mute, True],

            # ARGS: [hi|vi|a|b]
            'primary': [self.audio_server.set_primary, True],

            # ARGS: id
            # id = hardware input id
            'rnnoise': [self.audio_server.rnnoise, True],

            # ARGS: [a|b] id [None|STATE|set] [None|control]
            # 'set' is for saving a new control value, if used you HAVE to pass
            # control, you can ommit the second and third args to toggle 
            'eq': [self.audio_server.eq, True],

            # ARGS: [hi|a] id STATE
            # this will cleanup a hardware device and will not affect the config
            # useful when e.g. changing the device used in a hardware input strip
            'toggle-hd': [self.audio_server.toggle_hardware_device, False],

            # ARGS: [vi|b] id STATE
            # this will cleanup a virtual device and will not affect the config
            # useful when e.g. renaming the device
            'toggle-vd': [self.audio_server.toggle_virtual_device, False],

            # ARGS: [hi|vi] id
            # wont affect config
            'reconnect': [self.audio_server.reconnect, False],
            

            # ARGS: [a|b] id NEW_DEVICE
            # NEW_DEVICE is the name of the device
            'change_hd': [self.audio_server.change_hardware_device, True],

            # ARGS: [hi|vi|a|b] id vol
            # vol can be an absolute number from 0 to 153
            # you can also add and subtract
            'volume': [self.audio_server.volume, True],

            # ARGS: id vol
            # vol can ONLY be an absolute number from 0 to 153
            'app-volume': [self.audio_server.volume, False],

            # ARGS: id device [sink-input|source-output]
            'move-app-device': [self.audio_server.move_app_device, True],

            # ARGS: id [sink-input|source-output]
            'get-stream-volume': [self.audio_server.get_app_stream_volume, False],

            'get-config': [self.get_config, False],

            'save_config': [self.save_config,],
            
            # not ready
            'get-vd': [self.audio_server.get_virtual_devices, False],
            'get-hd': [self.audio_server.get_hardware_devices, False],
            'list-apps': [self.audio_server.get_virtual_devices, False],
            'rename': [self.audio_server.rename, True], 

        }

    # function to register as a signal handler to gracefully exit
    def handle_exit_signal(self, signum, frame):
        self.command_queue.put(('exit',))

    # TODO: if the daemon should clean up its virtual devices on exit, do that here
    def close_server(self):
        # self.audio_server
        self.save_config()
        self.audio_server.cleanup()

    # this function handles the connection requests
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
                    print('client connected ', addr)

                    # send id to client
                    conn.sendall(str.encode(str(id).rjust(4, '0')))

                    # Create a thread for the client
                    event_queue = SimpleQueue()
                    thread = threading.Thread(target=self.listen_to_client, 
                            args=(conn, event_queue, id), daemon=True)
                    thread.start()
                    self.client_handler_threads[id] = thread
                    self.client_handler_connections[id] = conn
                    self.event_queues[id] = event_queue
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
                    print(f'client {id} disconnect')
                    conn.shutdown(socket.SHUT_RDWR)
                    # Notify the main process that this client handler is closing, so it can free its resources
                    self.command_queue.put(('client_handler_exit', id))
                    self.client_exit_queue.put(id)
                    break

    def handle_command(self, data):
        decoded_data = data.decode()
        args = tuple(decoded_data.split(' '))
        print(args)

        if args[0] == 'exit':
            return False

        try:
            return (self.commands[args[0]][0](*args[1:]), self.commands[args[0]][1],)
            # if self.commands[args[0]](*args[1:]):
                # return decoded_data
        except TypeError:
            return ('Invalid number of arguments', False)
        except Exception as ex:
            print(ex)
            return (ex, False)

    def read_config(self):
        # if config exists XDG_CONFIG_HOME 
        if os.path.isfile(CONFIG_FILE):
            try:
                self.config = json.load(open(CONFIG_FILE))
            except:
                print('ERROR loading config file')
                sys.exit(1)

            # if config is outdated it will try to add missing keys
            if not 'version' in self.config or self.config['version'] != __version__:
                self.config['layout'] = 'default'
                config_orig = json.load(open(ORIG_CONFIG_FILE))
                self.config['version'] = __version__
                self.config['enable_vumeters'] = True

                if 'jack' not in self.config:
                    self.config['jack'] = {}
                for i in config_orig['jack']:
                    if i not in self.config['jack']:
                        self.config['jack'][i] = config_orig['jack'][i]

                for i in ['a', 'b', 'vi', 'hi']:
                    for j in config_orig[i]:
                        for k in config_orig[i][j]:
                            if not k in self.config[i][j]:
                                self.config[i][j][k] = config_orig[i][j][k]
                self.save_config()
        else:
            self.config = json.load(open(ORIG_CONFIG_FILE))
             
            self.config['version'] = __version__

            self.save_config()

    def get_config(self, args=None):
        if args == None:
            return json.dumps(self.config, ensure_ascii=False)
        else:
            args = args.split(':')
            print(args)
            config = self.config
            for arg in args:
                config = config[arg]

            if type(config) != dict:
                return config
            else:
                return json.dumps(config, ensure_ascii=False)


    def save_config(self):
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(self.config, outfile, indent='\t', separators=(',', ': '))
