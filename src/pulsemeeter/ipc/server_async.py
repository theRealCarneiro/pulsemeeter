import threading
import logging
import asyncio
from pydantic import ValidationError

from pulsemeeter import settings
from pulsemeeter.ipc import utils, socket_async
from pulsemeeter.schemas import ipc_schema
# from pulsemeeter.ipc.router import Router
from pulsemeeter.ipc.router import Blueprint
from pulsemeeter.model.config_model import ConfigModel

LISTENER_TIMEOUT = 2

LOG = logging.getLogger("generic")
CONFIG = ConfigModel()


class Server:
    '''
    Async server for the pulsemeeter ipc
    '''

    def __init__(self, sock_name: str = None):
        '''
            "sock_name" is the name of the socket file, should only be used for testing
        '''

        self.client_num: int = 0
        self.thread: threading.Thread = None
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.clients: dict = {}
        self.exit_flag: bool = False
        self.server_task: asyncio.Task = None
        self.server = None
        self.routes = {}
        self.tasks = {}
        self.server_tasks: dict[str, asyncio.Task] = {}

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'
            settings.PIDFILE = f'/tmp/pulsemeeter.{sock_name}.pid'

        # if self.is_running():
            # raise ConnectionAbortedError('Another instance is already running')

    def register_blueprint(self, blueprint: Blueprint):
        '''
        Register the routes of a blueprint
        '''
        for route_key, route in blueprint.routes.items():
            self.routes[route_key] = route

    def get_route(self, route_key: str):
        route = self.routes.get(route_key)
        if route is None:
            LOG.error('No routes for command "`%s"', route_key)

        return route

    def register_task(self, blueprint):
        for task_key, task in blueprint.tasks.items():
            self.tasks[task_key] = task
            self.server_tasks[task_key] = self.loop.create_task(task.command(self._notify))

    async def cancel_tasks(self):
        for _, task in self.server_tasks.items():
            task.cancel()
            # await task

    # def create_task(self, task_name, task_function, task_callback):
    #     # self.server_tasks[task_name] = asyncio.ensure_future(task_function(task_callback), loop=self.loop)
    #     self.server_tasks[task_name] = self.loop.create_task(task_function(task_callback))

    def start_server(self, daemon: bool = False) -> None:
        '''
        Start server loop in another thread
        '''
        server_ready = threading.Event()
        # self.loop = asyncio.new_event_loop()
        # self.loop.create_task()

        if daemon is False:
            self.thread = threading.Thread(target=self.loop.run_until_complete,
                                           args=(self._bind_socket(server_ready),),
                                           daemon=False)
            self.thread.start()
            server_ready.wait()

        # else:
        #     self._bind_socket(server_ready)

    def close_server(self):
        if self.loop is None:
            return

        asyncio.run_coroutine_threadsafe(self._close_server(), self.loop)
        self.thread.join()

    async def _bind_socket(self, ready) -> None:
        '''
        Start the async socket and querry clients
        '''
        server = await asyncio.start_unix_server(self._handle_client, settings.SOCK_FILE)
        self.server = server
        LOG.info('Server started')
        ready.set()
        try:
            async with server:
                await server.serve_forever()

        except asyncio.exceptions.CancelledError:
            for _, client in self.clients.items():
                client.writer.transport.close()
                client.writer.close()
                await client.writer.wait_closed()
            LOG.info('Server Closed')

        finally:
            pass

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        '''
        Handle client events
            "reader" is the StreamReader of the client
            "writer" is the StreamWriter of the client
        '''

        # set set client id and store writer
        self.client_num += 1
        client = socket_async.SocketAsync(reader=reader, writer=writer, client_id=self.client_num)
        self.clients[client.client_id] = client

        # send id to client
        await client.send_message(client.encoded_id)

        #  get listen flags and store
        subscription_flags = await client.get_message()
        client.set_subscription_flags(int(subscription_flags))

        LOG.debug('Client %d connected', client.client_id)

        # listen loop
        try:
            while not self.exit_flag:

                # get req
                req = await client.get_request()

                # handle request
                res = await self._handle_request(req)

                # send response
                await client.send_response(res)

                # notify
                if res.status == ipc_schema.StatusCode.OK:
                    self.loop.create_task(self._notify(req))

        # server/client closed the connection
        except asyncio.exceptions.IncompleteReadError:
            LOG.info('Connection closed with client #%d', client.client_id)
            writer.close()
            self.clients.pop(client.client_id)

        finally:
            self.exit_flag = True
            await self._close_server()

    async def _handle_request(self, req: ipc_schema.Request) -> ipc_schema.Response:
        '''
        Handles a request, returns a response
            "req" is a request
        '''
        LOG.debug(req)

        route = self.get_route(req.command)

        if req.command == 'exit':
            self.exit_flag = 1

        try:
            # validate request
            if route.schema_hint is not None:
                req = route.schema_hint(**req.data)
            else:
                req = None

        except ValidationError:
            LOG.info("Schema validation error, hint: %s, req: %s", route.schema_hint, req)
            status_code = ipc_schema.StatusCode.INVALID

        # run command
        ret_message = await route.command(req)
        status_code = ipc_schema.StatusCode.OK

        res = ipc_schema.Response(
            status=status_code,
            data=ret_message,
        )

        if route.save_config is True:
            CONFIG.write()

        return res

    async def _notify(self, req: ipc_schema.Request) -> None:
        '''
        Send event to clients
            "req" is the request
        '''
        for client_id, client in self.clients.items():

            # don't send event to client that triggered the event
            if client_id == req.sender_id or client.subscription_flags == 0:
                continue

            msg = req.encode()
            await client.send_message(msg)

    async def _close_server(self):

        # close connections
        for client in list(self.clients.values()):
            req = ipc_schema.Request(command='exit', sender_id=0, data={})
            await client.send_message(req.encode())
            client.writer.close()
            try:
                await client.writer.wait_closed()
            except Exception as e:
                LOG.error("Error closing client %d: %s", client.client_id, e)

        await self.cancel_tasks()
        await asyncio.sleep(0.1)

        CONFIG.write()
        self.server.close()
        await self.server.wait_closed()
