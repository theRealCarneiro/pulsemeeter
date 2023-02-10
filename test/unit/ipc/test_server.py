import unittest
import time

from meexer.ipc.server import Server
from meexer.ipc.client import Client


class TestIpc(unittest.TestCase):

    # def test_create(self):
        # s = Server(instance_name='test_create')
        # s.release_pid()

    # def test_create_twice(self):
        # s = Server(instance_name='test_create_twice')

        # with self.assertRaises(ConnectionAbortedError):
            # Server(instance_name='test_create_twice')

        # s.release_pid()

    def test_query_clients(self):
        s = Server(instance_name='test_query_clients')
        s.start_queries()
        time.sleep(0.2)
        # c = Client(instance_name='test_query_clients')
        # c.close_connection()
        s.stop_main_loop()
        s.exit_flag = True
        # s.stop_queries()
        # s.stop_main_loop()
        # s.release_pid()

    # def test_get_message(self):
        # s = Server(instance_name='test_get_message')

        # @s.command('connect', notify=True, flags=(2 | 4))
        # def test(a: dict):
            # return {'command': 'connect', 'data': {}, 'sender_id': '00000', 'flags': 0}

        # s.start_queries(daemon=True)
        # c = Client(instance_name='test_query_clients')
        # c.send_request('connect', {})
        # time.sleep(0.2)
        # c.close_connection()
        # s.release_pid()
        # s.stop_queries()

    # def test_listen(self):
        # s = Server(instance_name='test_listen')

        # @Server.command('connect', notify=True, flags=(2 | 4))
        # def test(a: dict):
            # return {'command': 'connect', 'data': {}, 'sender_id': '00000', 'flags': 0}

        # s.start_queries(daemon=True)
        # c = Client(instance_name='test_query_clients')
        # Client(listen_flags=1)
        # c.send_request('connect', {})
        # time.sleep(0.2)
        # c.close_connection()
        # s.release_pid()
        # s.stop_queries()


TestIpc().test_query_clients()
