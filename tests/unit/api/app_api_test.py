import unittest
from meexer.api import app_api
# from meexer.schemas import requests_schema


class TestAppList(unittest.TestCase):
    '''
    This is for testing creation and destruction of devices
    '''

    def test_app_list(self):
        app_api.app_list({'app_type': 'sink_input'})

    def test_app_move(self):
        app_api.app_move({'app_type': 'sink_input', 'app_index': 10, 'device': 'Main'})
