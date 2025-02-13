import threading
import logging
import socket
import json
import traceback

from meexer import settings
from meexer.ipc import utils
from meexer.ipc.socket import Socket
from meexer.schemas import ipc_schema

LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5

LOG = logging.getLogger("generic")


class Client(Socket):

    _clients = {}

    def __init__(self, listen_flags: int = 0, instance_name: str = 'default',
                 sock_name: str = None):
        '''
        '''

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.id = None
        self.listen_id = None
        self.listen_flags = listen_flags
        self.request_id = 0
        self.instance_name = instance_name
        self.exit_flag = False
        self.callbacks = {}

        # connect to server
        try:
            self.conn.connect(settings.SOCK_FILE)
            client_id = int(self.get_message())
            # self.conn.sendall(str(0).rjust(CLIENT_ID_LEN, '0').encode())
            LOG.debug('connected to server, id %d', client_id)
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

        super().__init__(self, sock, client_id)
        Client.new_client(self, instance_name)

        if listen_flags:
            self.start_listen()

    def callback(self, command_str):
        '''
        Decorator for creating callbacks
        '''
        def decorator(function):
            if command_str not in self.callbacks:
                self.callbacks[command_str] = []
            self.callbacks[command_str].append(function)
            return function

        return decorator

    def start_listen(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def close_connection(self) -> None:
        self.conn.close()

    def listen(self) -> None:
        '''
        Listen to server events and do callbacks
        '''

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(settings.SOCK_FILE)
            self.listen_id = int(sock.recv(CLIENT_ID_LEN))
            sock.sendall(utils.id_to_str(self.listen_flags))
            while not self.exit_flag:
                msg_dict = self.get_message(sock)
                req = ipc_schema.Request(**msg_dict)
                if req.sender_id != self.id:
                    print(req)

    def stop_listen(self) -> None:
        self.exit_flag = True

    @classmethod
    def new_client(cls, client, client_name: str = 'default'):
        cls._clients[client_name] = client

    @classmethod
    def get_client(cls, client_name: str = 'default'):
        return cls._clients.get(client_name)
