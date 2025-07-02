import threading
import logging
import asyncio
from pydantic import ValidationError
from pulsemeeter import settings
from pulsemeeter.schemas import ipc_schema
from pulsemeeter.ipc import socket_async, utils

LOG = logging.getLogger("generic")


class Client(socket_async.SocketAsync):

    _clients = {}

    def __init__(self, subscription_flags: int = 0, instance_name: str = 'default',
                 sock_name: str = None):

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.thread: threading.Thread = None
        self.loop: asyncio.AbstractEventLoop = None
        self.client_id: int = None
        self.exit_signal: bool = False
        self.listen_task = None
        self.subscription_flags = subscription_flags
        self.new_client(self, instance_name)

    def start(self) -> None:
        '''
        Start the client
        '''
        self.loop = asyncio.new_event_loop()
        event = threading.Event()
        self.loop.create_task(self._connect(event))
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=False)
        self.thread.start()
        event.wait()

    def close(self):
        self.listen_task.cancel()
        self.loop.stop()
        self.thread.join()

    async def _connect(self, client_ready: threading.Event) -> None:
        '''
        Connect to the server and start listening
        '''
        self.reader, self.writer = await asyncio.open_unix_connection(settings.SOCK_FILE)
        self.client_id = int(await self.get_message())
        self.send_message(utils.id_to_bytes(self.subscription_flags))  # listen flags
        LOG.info('Connected to server, id: %d', self.client_id)
        client_ready.set()
        self.listen_task = self.loop.create_task(self._listen())

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

    @classmethod
    def new_client(cls, client, client_name: str = 'default'):
        cls._clients[client_name] = client

    @classmethod
    def get_client(cls, client_name: str = 'default'):
        return cls._clients.get(client_name)
