import socket
import sys
import os
import signal
import threading
from queue import SimpleQueue
from .settings import SOCK_FILE


LISTENER_TIMEOUT = 5

class Server:
    def __init__(self, audio_server):

        # audio server can be pulse or pipe, so just use a generic name
        self.audio_server = audio_server

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
                ret_message = self.handle_command(message)
                self.event_queues[message[1]].put(('return', ret_message))

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

        # Set the exit flag and wait for the listener thread to timeout
        print(f'sending exit signal to listener thread, it should exit within {LISTENER_TIMEOUT} seconds...')
        self.exit_flag = True
        self.listener_thread.join()

        # Call any code to clean up virtual devices or similar
        self.close_server()

    # function to register as a signal handler to gracefully exit
    def handle_exit_signal(self, signum, frame):
        self.command_queue.put(('exit',))

    # TODO: if the daemon should clean up its virtual devices on exit, do that here
    def close_server(self):
        pass

    # this function handles the connection requests
    def query_clients(self):
        # loop to get new connections
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(LISTENER_TIMEOUT)
            s.bind(SOCK_FILE)
            s.listen()
            i = 0
            while True:
                try:
                    # Wait for a connection
                    print('waiting for a connection')
                    conn, addr = s.accept()
                    print('client connected ', addr)

                    # Create a thread for the client
                    event_queue = SimpleQueue()
                    thread = threading.Thread(target=self.listen_to_client, args=(conn, event_queue, i), daemon=True)
                    thread.start()
                    self.client_handler_threads[i] = thread
                    self.client_handler_connections[i] = conn
                    self.event_queues[i] = event_queue

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
                    data = conn.recv(20)
                    if not data: raise

                    print(data.decode())
                    self.command_queue.put(('command', data))
                    # TODO: If this handler is being used for sending events to clients, distinguish a return value from
                    # TODO: an event
                    ret_message = event_queue.get()
                    conn.sendall(ret_message[1])
                    if ret_message == False:
                        raise
                except Exception:  # Exception doesn't catch exit exceptions (a bare except clause does)
                    print('client disconnect')
                    conn.shutdown(socket.SHUT_RDWR)
                    # Notify the main process that this client handler is closing, so it can free its resources
                    self.command_queue.put(('client_handler_exit', id))
                    break

    # needs rework
    def handle_command(self, data):

        decoded_data = data.decode()
        cmd_list = decoded_data.split(' ')

        # command interpreter
        # need to add error handling

        # connect [vi|hi] [1-3] [a|b] [1-3]
        if cmd_list[0] == 'connect':
            if len(cmd_list) != 5: return
            source_index = [cmd_list[1], cmd_list[2]]
            sink_index = [cmd_list[3], cmd_list[4]]
            if self.audio_server.connect('connect', source_index, sink_index):
                msg = f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}{cmd_list[4]}:True'
                self.msg_queue.append(str.encode(msg))

        # disconnect [vi|hi] [1-3] [a|b] [1-3]
        if cmd_list[0] == 'disconnect':
            source_index = [cmd_list[1], cmd_list[2]]
            sink_index = [cmd_list[3], cmd_list[4]]
            if self.audio_server.connect('disconnect', source_index, sink_index):
                return str.encode(f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}{cmd_list[4]}:False')

        # vol [vi|hi|a|b] [1-3]
        if cmd_list[0] == 'vol':
            device_index = [cmd_list[1], cmd_list[2]]
            volume = cmd_list[3]
            if self.audio_server.volume(device_index, volume):
                return str.encode(f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}')

        if cmd_list[0] == 'mute':
            device_index = [cmd_list[1], cmd_list[2]]

        if cmd_list[0] == 'exit':
            return False

        return b' '


class Client:
    def __init__(self, command=None, is_listen=False):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
        except socket.error as msg:
            print(msg)
            sys.exit(1)
            if is_listen == True: self.listen()

    def send_command(self, command):
        try:
            if len(command) == 0: raise
            message = str.encode(command)
            self.sock.sendall(message)
            # print(self.sock.recv(20))
        except:
            print('closing socket')
            self.sock.close()

    def listen(self):
        while True:
            try:
                print(self.sock.recv(20))
            except:
                print('closing socket')
                self.sock.close()
                break

    def close_connection(self):
        print('closing socket')
        self.sock.close()
