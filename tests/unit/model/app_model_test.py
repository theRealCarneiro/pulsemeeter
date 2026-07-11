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


class TestDisplayDevice(unittest.TestCase):

    @staticmethod
    def _model(device='Music', pinned=False, object_id=None):
        return AppModel(app_type='sink_input', index=1, label='app', icon=None,
                        volume=100, mute=False, device=device,
                        pinned=pinned, object_id=object_id)

    def test_pinned_shows_device(self):
        assert self._model(device='Music', pinned=True).display_device == 'Music'

    def test_unpinned_shows_blank(self):
        assert self._model(device='Music', pinned=False).display_device == ''

    def test_defaults(self):
        model = self._model()
        assert model.object_id is None
        assert model.pinned is False
        assert model.display_device == ''
