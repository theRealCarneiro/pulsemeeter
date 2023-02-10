import threading
import logging
import socket
import json
import traceback

from meexer import settings
from meexer.schemas import ipc_schema

LISTENER_TIMEOUT = 2
CLIENT_ID_LEN = 5
REQUEST_SIZE_LEN = 5

LOG = logging.getLogger("generic")


class Client:

    def __init__(self, listen_flags: int = 0, instance_name: str = None):
        '''
        '''

        if instance_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{instance_name}.sock'

        self.conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.id = None
        self.listen_flags = listen_flags
        self.exit_flag = False

        # connect to server
        try:
            self.conn.connect(settings.SOCK_FILE)
            self.id = int(self.conn.recv(CLIENT_ID_LEN))
            self.conn.sendall(str(listen_flags).rjust(CLIENT_ID_LEN, '0').encode())
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

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

    def get_message(self) -> ipc_schema.Request:
        '''
        Retrives a single message from the server
        '''
        res = self.conn.recv(REQUEST_SIZE_LEN)
        msg_len = int(res.decode())

        res = self.conn.recv(msg_len)
        res = json.loads(res.decode())
        return ipc_schema.Request(**res)

    def listen(self) -> None:
        '''
        Listen to server events and do callbacks
        '''
        while not self.exit_flag:
            req = self.get_message()
            LOG.debug('Event %s', req)

    def send_message(self, req: str) -> None:
        '''
        Sends a single message to the server
        '''
        msg = req.encode('utf-8')
        msg_len = len(msg)
        if msg_len == 0: raise ValueError('Empty message not allowed')
        msg_len = str(msg_len).rjust(REQUEST_SIZE_LEN, '0').encode('utf-8')
        self.conn.sendall(msg_len)
        self.conn.sendall(msg)

    def send_request(self, command: str, data: dict):
        sid = str(self.id).rjust(CLIENT_ID_LEN, '0')
        r = {'command': command, 'data': data, 'sender_id': sid, 'flags': 0}
        req = ipc_schema.Request(**r)
        self.send_message(req.json())

        if not self.listen_flags:
            res = self.get_message()
            LOG.debug('Response %s', res)
