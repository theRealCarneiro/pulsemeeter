import unittest
from pulsemeeter.model.app_model import AppModel


class TestClassFunctions(unittest.TestCase):

    def test_list_apps(self):
        app_list = AppModel.list_apps('sink_input')
        assert isinstance(app_list, list)
        if len(app_list) > 0:
            assert isinstance(app_list[0], AppModel)

    def test_device_by_id(self):
        app_list = AppModel.list_apps('sink_input')
        if len(app_list) > 0:
            app = AppModel.get_app_by_id(app_list[0].index, 'sink_input')
            assert isinstance(app, AppModel)
