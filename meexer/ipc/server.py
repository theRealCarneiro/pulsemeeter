import threading
# import traceback
import logging
import socket
import json
import os

from queue import SimpleQueue

from meexer import settings
from meexer.ipc import utils
from meexer.schemas import ipc_schema as schemas
from meexer.settings import CLIENT_ID_LEN, REQUEST_SIZE_LEN

from meexer.ipc.router import Router

LISTENER_TIMEOUT = 2

LOG = logging.getLogger("generic")


class Server:

    def __init__(self, sock_name: str = None):
        '''
            "sock_name" is the name of the socket file, should only be used for testing
        '''

        if sock_name is not None:
            settings.SOCK_FILE = f'/tmp/pulsemeeter.{sock_name}.sock'
            settings.PIDFILE = f'/tmp/pulsemeeter.{sock_name}.pid'

        if self.is_running():
            # LOG.error('Another instance is already running')
            raise ConnectionAbortedError('Another instance is already running')

        # delete socket file if exists
        self.unlink_socket()

        self.exit_flag = False
        self.command_queue = SimpleQueue()
        self.query_thread = None
        self.main_loop_thread = None
        self.clients = {}

    def start_queries(self, daemon=False):
        '''
        Start query and server threads
            "daemon" is a bool, if True the server will exit when the main thread exists
                else it will remain running
        '''
        self.stop_queries()
        self.stop_main_loop()

        # self.ready = False
        self.query_thread = threading.Thread(target=self.query_clients, daemon=daemon)
        self.query_thread.start()

        self.main_loop_thread = threading.Thread(target=self.main_loop)
        self.main_loop_thread.start()

        # while not self.ready:
            # pass

    def stop_main_loop(self):
        if self.main_loop_thread is not None and self.main_loop_thread.is_alive():
            self.exit_flag = True
            self.main_loop_thread.join()

    def stop_queries(self):
        if self.query_thread is not None and self.query_thread.is_alive():
            self.exit_flag = True
            self.query_thread.join()

    def main_loop(self):
        '''
        Will run the commands requested by the clients
        '''

        # Make sure that even in the event of an error, cleanup still happens
        try:

            # Listen for commands
            while not self.exit_flag:
                req = self.command_queue.get()
                route = Router.get_route(req.command)

                if route is None:
                    LOG.error('No routes for command "`%s"', req.command)

                # close server without warning
                if req.command == 'kill':
                    break

                if route is None:
                    continue

                command_notify = route.notify
                command_flags = route.flags
                command_function = route.command

                if req.command == 'exit':
                    self.exit_flag = True

                # run function if command not from server
                if req.run is True:

                    # run command
                    status_code, ret_message = command_function(req.data)

                    res = schemas.Response(
                        status=status_code,
                        data=ret_message,
                        id=req.id
                    )

                    self.send_message(self.clients[int(req.sender_id)], res)

                    # skip notify when command fail
                    if status_code != schemas.StatusCode.OK:
                        continue

                if command_notify:
                    self.notify(req, command_flags)

        finally:

            # Set the exit flag and wait for the listener thread to timeout
            LOG.info('closing listener threads, they should exit within a few seconds...')
            self.exit_flag = True

            # try:
                # self.pulse_socket.stop_listener()
            # except Exception:
                # LOG.error('Could not close pulse listener')
                # LOG.error(traceback.format_exc())

            # Call any code to clean up virtual devices or similar
            # self.save_config(buffer=False)
            # if self.config['cleanup']:
                # self.cleanup()

    def query_clients(self) -> None:
        '''
        Loops for new connections
        '''

        # loop to get new connections
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(LISTENER_TIMEOUT)
            sock.bind(settings.SOCK_FILE)
            sock.listen()
            # server is id 0
            client_id = 1
            self.ready = True
            while not self.exit_flag:
                try:
                    # Wait for a connection
                    conn, addr = sock.accept()
                    LOG.debug('new client %d', client_id)

                    # send id to client
                    conn.sendall(utils.id_to_str(client_id))
                    flags = int(conn.recv(CLIENT_ID_LEN))

                    # Create a thread for the client
                    thread = threading.Thread(target=self.listen_client,
                            args=(client_id,), daemon=True)

                    client = schemas.Client(
                        conn=conn,
                        id=client_id,
                        thread=thread,
                        flags=flags
                    )

                    self.clients[client_id] = client
                    client.thread.start()
                    client_id += 1
                except socket.timeout:
                    if self.exit_flag:
                        break

    def listen_client(self, client_id) -> None:
        '''
        Listens to client and queue their requests
        '''
        client = self.clients[client_id]
        with client.conn:
            while not self.exit_flag:

                try:
                    req = self.recive_message(client)
                    LOG.debug(req)
                    self.command_queue.put(req)
                    # # TODO: save config
                    # if route.save_config:
                        # pass
                except (ConnectionResetError, ValueError):
                    LOG.debug('client #%d closed the connection', client_id)
                    self.clients.pop(client_id, None)
                    break

    def send_message(self, client: schemas.Client, res: schemas.Request) -> None:
        '''
        Send a message to a specific client
        '''

        # don't send message to id 0 since it's the server
        if int(client.id) == 0:
            return

        msg = res.json().encode('utf-8')
        msg_len = utils.msg_len_to_str(len(msg))
        client.conn.sendall(msg_len)
        client.conn.sendall(msg)

    def notify(self, req: schemas.Request, command_flags: int) -> None:
        '''
        Send events to subscribed clients
        '''
        sender_id = req.sender_id
        for client_id, client in self.clients.items():
            if client_id != sender_id:

                # check if client wants notification
                if client.flags & command_flags:
                    self.send_message(client, req)

    def get_message(self, conn) -> str:
        '''
        Recives a connection, and returns a single massage
        '''
        msg_len = conn.recv(REQUEST_SIZE_LEN)
        if not msg_len: raise ValueError('Invalid message length')
        msg_len = int(msg_len.decode())

        msg = conn.recv(msg_len)
        if not msg: raise ValueError('Invalid message data')

        return msg

    def recive_message(self, client: schemas.Client) -> schemas.Request:
        '''
        Recives a client, returns a request
        '''
        msg = self.get_message(client.conn)
        req = json.loads(msg.decode())
        LOG.debug(req)
        return schemas.Request(**req)

    def unlink_socket(self):
        '''
        Deletes socket file
        '''
        try:
            os.unlink(settings.SOCK_FILE)
        except OSError:
            if os.path.exists(settings.SOCK_FILE):
                raise

    def unlink_pid_file(self):
        '''
        Deletes pid file
        '''
        try:
            os.unlink(settings.PIDFILE)
        except OSError:
            if os.path.exists(settings.PIDFILE):
                raise

    def exit_signal(self):
        '''
        Inserts an exit command on the command queue for a clean exit
        '''
        req = schemas.Request(
            command='exit',
            sender_id=utils.id_to_str(0),
            data={},
            id=0,
            flags=0
        )

        self.command_queue.put(req)

    def kill_signal(self):
        '''
        Inserts a kill command on the command queue for an imediate exit
        '''
        req = schemas.Request(
            command='kill',
            sender_id=utils.id_to_str(0),
            data={},
            id=0,
            flags=0
        )

        self.command_queue.put(req)

    def is_running(self):

        try:
            with open(settings.PIDFILE) as f:
                pid = int(next(f))

            # if pid is of running instance
            if os.kill(pid, 0) is not False:
                return True

            # if pid is of a closed instance
            else:
                # write pid to file
                with open(settings.PIDFILE, 'w') as f:
                    f.write(f'{os.getpid()}\n')
                return False

        # PIDFILE does not exist
        except Exception:
            with open(settings.PIDFILE, 'w') as f:
                f.write(f'{os.getpid()}\n')
            return False
