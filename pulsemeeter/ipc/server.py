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
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(LISTENER_TIMEOUT)
            s.bind(SOCK_FILE)
            s.listen()
            id = 0
            while not self.exit_flag:
                try:
                    # Wait for a connection
                    conn, addr = s.accept()
                    LOG.debug(f'new client {id}')

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
                    if not msg_len: raise
                    msg_len = int(msg_len.decode())

                    data = conn.recv(msg_len)
                    if not data: raise

                    # print(data, msg_len)
                    LOG.debug(f'message from client #{id}, size {msg_len}: {data}')
                    if data == b'quit': raise

                    self.command_queue.put(('command', id, data))
                except Exception:
                    LOG.debug(f'client {id} disconnect')
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
                LOG.info(f'client {sender_id} already disconnected, message not sent')

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
    if type(s) is bytes:
        return s
    elif type(s) is str:
        return codecs.encode(s, 'utf-8')
    else:
        raise TypeError(f"[ERROR] [function: to_bytes()@{__name__}] Expected bytes or string, but got {type(s)}.")
