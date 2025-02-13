import logging
import asyncio
import json

from meexer.settings import REQUEST_SIZE_LEN
from meexer.schemas import ipc_schema
from meexer.ipc import utils


LOG = logging.getLogger("generic")


class SocketAsync:

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: int):
        self.reader = reader
        self.writer = writer
        self.client_id = client_id
        self.encoded_id = utils.id_to_bytes(client_id)

    # @property
    # def encoded_id(self) -> bytes:
    #     return utils.id_to_bytes(self.client_id)

    async def get_message(self) -> str:
        '''
        Get a message
        '''

        msg_len: bytes = await self.reader.readexactly(REQUEST_SIZE_LEN)
        int_msg_len = int(msg_len)
        LOG.debug("Recieving message len: %d", int_msg_len)

        msg: bytes = await self.reader.readexactly(int_msg_len)
        if not msg:
            raise ConnectionAbortedError()

        msg_decoded = msg.decode('utf-8')
        LOG.debug("Recieving message: %s", msg_decoded)

        return msg_decoded

    async def send_message(self, msg: bytes) -> None:
        '''
        Send a msg
            "req" is the req object
        '''

        msg_len: bytes = utils.msg_len_to_bytes(len(msg))

        LOG.debug('Sending message len: %s', msg_len)
        self.writer.write(msg_len)
        await self.writer.drain()

        LOG.debug('Sending message: %s', msg)
        self.writer.write(msg)
        await self.writer.drain()

    async def get_response(self) -> ipc_schema.Response:
        '''
        Read msg from client and convert to Request
        '''

        msg: str = await self.get_message()
        msg_dict: dict = json.loads(msg)
        res: ipc_schema.Response = ipc_schema.Response(**msg_dict)
        return res

    async def get_request(self) -> ipc_schema.Request:
        '''
        Read msg from client and convert to Request
        '''

        msg = await self.get_message()
        msg_dict = json.loads(msg)
        req: ipc_schema.Request = ipc_schema.Request(**msg_dict)
        return req

    async def send_response(self, res: ipc_schema.Response):
        msg = res.encode()
        await self.send_message(msg)

    async def send_request(self, command: str, data: dict, sender_id: int) -> ipc_schema.Response:
        '''
        Send a request to the server
            "req" is the req object
        '''

        req = ipc_schema.Request(
            command=command,
            sender_id=sender_id,
            data=data
        )

        msg_enc = req.encode()
        await self.send_message(msg_enc)
        res = await self.get_response()
        return res
