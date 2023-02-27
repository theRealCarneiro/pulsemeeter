import threading
import logging
import socket
import json
import traceback

from meexer import settings
from meexer.ipc import utils
from meexer.schemas import ipc_schema

LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5

LOG = logging.getLogger("generic")


class Client:

    _clients = {}

    def __init__(self, listen_flags: int = 0, instance_name: str = 'default',
                 sock_name: str = None):
        '''
        '''

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'

        self.conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.id = None
        self.listen_flags = listen_flags
        self.request_id = 0
        self.instance_name = instance_name
        self.exit_flag = False

        # connect to server
        try:
            self.conn.connect(settings.SOCK_FILE)
            self.id = int(self.conn.recv(CLIENT_ID_LEN))
            self.conn.sendall(str(0).rjust(CLIENT_ID_LEN, '0').encode())
            LOG.debug('connected to server, id %d', self.id)
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

        Client.new_client(self, instance_name)

        if listen_flags:
            self.start_listen()

    def callback(self, command_str, flags=0, notify=False, save_config=False):
        '''
        Decorator for creating callbacks
        '''
        def decorator(f):
            if command_str not in self.callbacks:
                self.callbacks[command_str] = []
            self.routes[command_str].append(f)
            return f

        return decorator

    def start_listen(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def close_connection(self) -> None:
        self.conn.close()

    def get_message(self, sock: socket.socket = None) -> dict:
        '''
        Retrives a single message from the server
        '''
        if sock is None:
            sock = self.conn

        res = sock.recv(REQUEST_SIZE_LEN)
        msg_len = int(res.decode())

        msg = sock.recv(msg_len)
        msg_dict = json.loads(msg.decode())
        return msg_dict

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

    def send_message(self, req: ipc_schema.Request) -> None:
        '''
        Send a request to server
        '''
        json_string = req.json()
        msg = json_string.encode('utf-8')
        msg_len = len(msg)
        if msg_len == 0: raise ValueError('Empty message not allowed')
        self.conn.sendall(utils.msg_len_to_str(msg_len))
        self.conn.sendall(msg)

    def send_request(self, command: str, data: dict) -> ipc_schema.Response:
        '''
        Create a request and send it to server
        '''
        req = ipc_schema.Request(
            command=command,
            data=data,
            sender_id=self.id,
            id=self.request_id,
            flags=0
        )
        self.send_message(req)

        msg = self.get_message()
        res = ipc_schema.Response(**msg)
        LOG.debug('Response %s', res)

        self.request_id += 1
        return res

    @classmethod
    def new_client(cls, client, client_name: str = 'default'):
        cls._clients[client_name] = client

    @classmethod
    def get_client(cls, client_name: str = 'default'):
        return cls._clients.get(client_name)
