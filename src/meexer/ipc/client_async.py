import threading
import logging
import asyncio
from pydantic import ValidationError
from meexer import settings
from meexer.schemas import ipc_schema
from meexer.ipc import utils

LOG = logging.getLogger("generic")


class Client:

    _clients = {}

    def __init__(self, listen_flags: int = 0, instance_name: str = 'default',
                 sock_name: str = None):

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.thread: threading.Thread = None
        self.loop: asyncio.AbstractEventLoop = None
        self.default_id: int = None
        self.exit_signal: bool = False
        self.listen_flags = listen_flags
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

    def send_request(self, command: str, data: dict) -> ipc_schema.Response:
        '''
        Send a request to the server, returns an answer
            "command" is the str command
            "data" is the data of the request
        '''
        future = asyncio.run_coroutine_threadsafe(
            utils.send_request(self.writer, self.reader, command, data, self.default_id), self.loop
        )
        res: ipc_schema.Response = future.result()
        return res

    async def _connect(self, client_ready: threading.Event) -> None:
        '''
        Connect to the server and start listening
        '''
        self.reader, self.writer = await asyncio.open_unix_connection(settings.SOCK_FILE)
        self.default_id = int(await utils.get_message(self.reader))
        LOG.info('Connected to server, id: %d', self.default_id)
        client_ready.set()
        self.listen_task = self.loop.create_task(self._listen())

    async def _listen(self) -> None:
        '''
        Listen to events
        '''

        while not self.exit_signal:
            msg = await utils.get_message(self.reader)
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
