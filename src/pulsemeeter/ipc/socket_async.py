import threading
import logging
import asyncio
import json

from pydantic import ValidationError

from pulsemeeter.settings import REQUEST_SIZE_LEN
from pulsemeeter.schemas import ipc_schema
from pulsemeeter.ipc import utils
from pulsemeeter import settings


LOG = logging.getLogger("generic")


class SocketAsync:

    reader:             asyncio.StreamReader
    writer:             asyncio.StreamWriter
    client_id:          int

    thread:             threading.Thread
    loop:               asyncio.AbstractEventLoop
    listen_task:        asyncio.Task

    subscription_flags: ipc_schema.SubscriptionFlags = 0
    exit_signal:        bool = False

    # def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: int, flags=0):
    #     self.reader = reader
    #     self.writer = writer
    #     self.client_id = client_id
    #     self.subscription_flags: ipc_schema.SubscriptionFlags = 0
    #
    #     self.encoded_id = utils.id_to_bytes(client_id)

    def set_subscription_flags(self, subscription_flags):
        self.subscription_flags = subscription_flags

    async def handshake(self) -> None:
        '''
        Connect to the server and start listening
        '''
        event = threading.Event()

        self.loop = asyncio.new_event_loop()
        self.loop.create_task(self._connect(event))
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=False)
        self.thread.start()
        event.wait()

    async def _connect(self, client_ready: threading.Event):
        self.reader, self.writer = await asyncio.open_unix_connection(settings.SOCK_FILE)
        self.client_id = int(await self.get_message())
        self.send_message(utils.id_to_bytes(self.subscription_flags))  # listen flags
        LOG.info('Connected to server, id: %d', self.client_id)

        client_ready.set()
        self.listen_task = self.loop.create_task(self._listen())

    @property
    def encoded_id(self) -> bytes:
        return utils.id_to_bytes(self.client_id)

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

    async def _listen(self) -> None:
        '''
        Listen to events
        '''

        while not self.exit_signal:
            msg = await self.get_message()
            try:
                req = ipc_schema.Request.parse_raw(msg)
                LOG.debug(req)
            except ValidationError:
                res = ipc_schema.Response.parse_raw(msg)

            # handle event
