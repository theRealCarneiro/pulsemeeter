import threading
import logging
import socket
import traceback

from pulsemeeter import settings
from pulsemeeter.ipc import utils
from pulsemeeter.ipc.socket import Socket
from pulsemeeter.schemas import ipc_schema

LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5

LOG = logging.getLogger("generic")


class Client(Socket):

    _clients = {}
    _callbacks = {}

    def __init__(self, subscription_flags: int = 0, instance_name: str = 'default',
                 sock_name: str = None):
        '''
        '''

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'

        self.listen_id = None
        self.subscription_flags = subscription_flags
        self.instance_name = instance_name
        self.exit_flag = False
        self.callbacks = {}
        super().__init__()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # connect to server
        if subscription_flags == 0:
            self.client_id: int = self.handshake()
            Client.new_client(self, instance_name)

        if subscription_flags:
            self.start_listen()

    def handshake(self) -> int:
        '''
        Performs the handshake with the server
        returns client id
        '''
        try:
            self.sock.connect(settings.SOCK_FILE)
            client_id = int(self.get_message())
            self.send_message(utils.id_to_bytes(0))  # listen flags
            LOG.debug('Connected to server, id: %d', client_id)
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

        return client_id

    # def callback(self, command_str):
    #     '''
    #     Decorator for creating callbacks
    #     '''
    #     def decorator(function):
    #         if command_str not in self.callbacks:
    #             self.callbacks[command_str] = []
    #         self.callbacks[command_str].append(function)
    #         return function
    #
    #     return decorator

    def start_listen(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def close_connection(self) -> None:
        self.sock.close()

    def listen(self) -> None:
        '''
        Listen to server events and do callbacks
        '''

        with self.sock as sock:
            sock.connect(settings.SOCK_FILE)
            _ = int(self.get_message())

            self.send_message(str(ipc_schema.SubscriptionFlags.ALL).encode(encoding='utf-8'))

            while not self.exit_flag:
                req = self.get_request()
                if req.command == 'exit':
                    break
                callback = self.get_callback(req.command)
                if callback is not None:
                    callback(req.data)

    def stop_listen(self) -> None:
        self.exit_flag = True

    def create_callback(self, command_str, function):

        # quick hack to get the type hint
        # def decorator(function):

        self.callbacks[command_str] = function

    def get_callback(self, command_str):
        return self.callbacks.get(command_str)

    @classmethod
    def new_client(cls, client, client_name: str = 'default'):
        cls._clients[client_name] = client

    @classmethod
    def get_client(cls, client_name: str = 'default'):
        return cls._clients.get(client_name)
