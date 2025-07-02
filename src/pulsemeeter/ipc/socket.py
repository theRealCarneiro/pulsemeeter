import traceback
import logging
import socket
import json

from typing import Callable

from pulsemeeter import settings
from pulsemeeter.schemas import ipc_schema
from pulsemeeter.ipc import utils
# from pulsemeeter.ipc.socket import Socket


LOG = logging.getLogger("generic")


class Socket:

    sock: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_id: int
    encoded_id: bytes
    subscription_flags: int = ipc_schema.SubscriptionFlags.NO_LISTEN
    callbacks: dict[str, Callable] = {}

    _exit_flag: bool = False

    def set_subscription_flags(self, subscription_flags):
        self.subscription_flags = subscription_flags

    def handshake(self) -> int:
        '''
        Performs the handshake with the server
            returns client id
        '''
        # if self.sock is None:
        #     socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            self.sock.connect(settings.SOCK_FILE)
            encoded_id = self.get_message()
            client_id = int(encoded_id)
            self.send_message(utils.id_to_bytes(0))  # listen flags
            LOG.debug('Connected to server, id: %d', client_id)
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

        self.client_id = client_id
        return client_id

    def get_message(self) -> str:
        '''
        Get a message
        '''

        # get msg length
        msg_len: bytes = self.sock.recv(settings.REQUEST_SIZE_LEN)
        int_msg_len = int(msg_len)
        LOG.debug("Recieved message len: %d", int_msg_len)

        # get msg
        msg: bytes = self.sock.recv(int_msg_len)
        if not msg:
            raise ConnectionAbortedError()
        msg_decoded = msg.decode('utf-8')
        LOG.debug("Recieving message: %s", msg_decoded)

        return msg_decoded

    def send_message(self, msg: bytes) -> None:
        '''
        Send a msg
            "req" is the req object
        '''

        msg_len: bytes = utils.msg_len_to_bytes(len(msg))

        LOG.debug('Sending message len: %s', msg_len)
        self.sock.sendall(msg_len)

        LOG.debug('Sending message: %s', msg)
        self.sock.sendall(msg)

    def get_response(self) -> ipc_schema.Response:
        '''
        Read msg from client and convert to Request
        '''

        msg: str = self.get_message()
        # print()
        # print(msg)
        # print()
        msg_dict: dict = json.loads(msg)
        res: ipc_schema.Response = ipc_schema.Response(**msg_dict)
        return res

    def get_request(self) -> ipc_schema.Request:
        '''
        Read msg from client and convert to Request
        '''

        msg = self.get_message()
        msg_dict = json.loads(msg)
        req: ipc_schema.Request = ipc_schema.Request(**msg_dict)
        return req

    def send_response(self, res: ipc_schema.Response):
        msg = res.encode()
        self.send_message(msg)

    def send_request(self, command: str, data: dict) -> ipc_schema.Response:
        '''
        Send a request to the server
            "req" is the req object
        '''

        req = ipc_schema.Request(
            command=command,
            sender_id=self.client_id,
            data=data
        )

        msg_enc = req.encode()
        self.send_message(msg_enc)
        res: ipc_schema.Response = self.get_response()
        return res

    def create_callback(self, command_str, function):
        self.callbacks[command_str] = function

    def get_callback(self, command_str):
        return self.callbacks.get(command_str)

    def listen(self):
        '''
        Listen to server events and do callbacks
        '''

        with self.sock as sock:
            _ = self.handshake()
            self.send_message(str(ipc_schema.SubscriptionFlags.ALL).encode(encoding='utf-8'))
            while not self._exit_flag:
                req = self.get_request()

                if req.command == 'exit':
                    break

                callback = self.get_callback(req.command)
                if callback is None:
                    continue

                callback(req.data)

    def stop_listen(self) -> None:
        self._exit_flag = True
