import threading
import logging
import socket
import codecs
import os

from queue import SimpleQueue

from pulsemeeter.settings import SOCK_FILE, PIDFILE

LISTENER_TIMEOUT = 2

LOG = logging.getLogger("generic")


class Server:
    def __init__(self, auto_start=True):

        # delete socket file if exists
        try:
            if self.is_running():
                LOG.error('Another instane is already running')
                raise ConnectionAbortedError('Another copy is already running')
            os.unlink(SOCK_FILE)
        except OSError:
            if os.path.exists(SOCK_FILE):
                raise

        self.exit_flag = False
        self.command_queue = SimpleQueue()
        self.client_handler_threads = {}
        self.client_handler_connections = {}

        if auto_start: self.start_query()

    def start_query(self):

        self.query_thread = threading.Thread(target=self.query_clients)
        self.query_thread.start()

    def stop_server(self, signum=None, frame=None):
        self.command_queue.put(('exit', None, 'exit'))

    # handles connection requests
    def query_clients(self):
        # loop to get new connections
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(LISTENER_TIMEOUT)
            sock.bind(SOCK_FILE)
            sock.listen()
            id = 0
            while not self.exit_flag:
                try:
                    # Wait for a connection
                    conn, addr = sock.accept()
                    LOG.debug('new client %d', id)

                    # send id to client
                    conn.sendall(str.encode(str(id).rjust(4, '0')))

                    # Create a thread for the client
                    thread = threading.Thread(target=self.listen_to_client,
                            args=(conn, id), daemon=True)
                    self.client_handler_connections[id] = conn
                    self.client_handler_threads[id] = thread
                    thread.start()
                    id += 1
                except socket.timeout:
                    if self.exit_flag:
                        break

    # get data stream and pass it into command handling function
    def listen_to_client(self, conn, id):
        with conn:
            while not self.exit_flag:

                try:
                    msg_len = conn.recv(4)
                    if not msg_len: raise Exception
                    msg_len = int(msg_len.decode())

                    data = conn.recv(msg_len)
                    if not data: raise Exception

                    # print(data, msg_len)
                    LOG.debug('message from client #%d, size %d: %s', id, msg_len, data)
                    if data == b'quit': raise Exception

                    self.command_queue.put(('command', id, data))
                except Exception:
                    LOG.debug('client %d disconnect', id)
                    conn.shutdown(socket.SHUT_RDWR)
                    del self.client_handler_connections[id]
                    break

    def close_server(self):
        self.exit_flag = True

    def send_message(self, ret_message, sender_id, notify_all):
        encoded_msg = to_bytes(ret_message)
        # encoded_msg = ret_message.encode()

        client_list = []
        # notify all observers
        if notify_all:
            client_list = self.client_handler_connections.values()

        # notify only the client that sent the command
        elif sender_id in self.client_handler_connections:
            client_list = [self.client_handler_connections[sender_id]]

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
                LOG.info('client %d already disconnected, message not sent', sender_id)

    def is_running(self):
        try:
            with open(PIDFILE) as f:
                pid = int(next(f))

            # if pid is of running instance
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

    def handle_command(self, command):
        return '{}', False
        # raise NotImplementedError


def to_bytes(s):
    if isinstance(s, bytes):
        return s

    if isinstance(s, str):
        return codecs.encode(s, 'utf-8')

    raise TypeError(f"[ERROR] [function: to_bytes()@{__name__}] Expected bytes or string, but got {type(s)}.")
