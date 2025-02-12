import unittest
import time

from meexer.ipc.server import Server
from meexer.ipc.router import Blueprint
from meexer.ipc.client import Client
from meexer.schemas.ipc_schema import Request, StatusCode


class TestIpc(unittest.TestCase):

    def test_create(self):
        s = Server(sock_name='test_create')
        s.kill_signal()
        # s.release_pid()

    # def test_create_twice(self):
        # s = Server(sock_name='test_create_twice')

        # with self.assertRaises(ConnectionAbortedError):
            # Server(sock_name='test_create_twice')

        # s.kill_signal()

    # def test_query_clients(self):
        # s = Server(sock_name='test_query_clients')
        # s.start_queries()
        # time.sleep(0.2)
        # c = Client(sock_name='test_query_clients')
        # c.close_connection()
        # s.kill_signal()

    # def test_get_message(self):

        # ipc = Blueprint('test_get_message')

        # @ipc.command('test_get_message', notify=True, flags=2 | 4)
        # def test(a: dict):
            # return StatusCode.OK, a

        # s = Server(sock_name='test_get_message')
        # s.register_blueprint(ipc)
        # s.start_queries(daemon=True)
        # time.sleep(0.2)
        # c = Client(sock_name='test_get_message')
        # test_data = {'test_data': 'test_data'}
        # res = c.send_request('test_get_message', test_data)
        # assert test_data == res.data
        # c.close_connection()
        # s.kill_signal()

    # def test_client_listen(self):
        # s = Server(sock_name='test_listen')
        # s.start_queries()
        # time.sleep(0.2)
        # c = Client(sock_name='test_listen', listen_flags=1)
        # time.sleep(0.2)
        # test_data = {'test_data': 'test_data'}
        # req = Request(command='test_listen', sender_id=0, data=test_data, id=0)
        # s.send_message(s.clients[2], req)
        # time.sleep(0.2)
        # c.stop_listen()
        # c.close_connection()
        # s.kill_signal()
