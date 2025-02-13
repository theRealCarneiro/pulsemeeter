import logging
import json
import socket

from meexer.settings import REQUEST_SIZE_LEN
from meexer.schemas import ipc_schema
from meexer.ipc import utils


LOG = logging.getLogger("generic")


class Socket:
    sock: socket.socket
    client_id: int
    encoded_id: bytes

    # def __init__(self, sock: socket.socket, client_id: int):
    #     self.sock = sock
    #     self.client_id = client_id
    #     self.encoded_id = utils.id_to_bytes(client_id)

    def get_message(self) -> str:
        '''
        Get a message
        '''

        # get msg length
        msg_len: bytes = self.sock.recv(REQUEST_SIZE_LEN)
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
