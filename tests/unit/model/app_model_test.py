import unittest

from pulsemeeter.model.app_model import AppModel


class _FakeVolume:
    def __init__(self, values):
        self.values = values


class _FakePaApp:
    '''Minimal stand-in for a pulsectl PulseSinkInputInfo/PulseSourceOutputInfo.'''
    def __init__(self, index, name, values, mute=False, icon=None, device_name='Main'):
        self.index = index
        self.volume = _FakeVolume(values)
        self.mute = mute
        self.device_name = device_name
        self.proplist = {'application.name': name}
        if icon is not None:
            self.proplist['application.icon_name'] = icon


def _app(**overrides):
    kwargs = {
        'app_type': 'sink_input',
        'index': 1,
        'label': 'test_app',
        'icon': 'audio-card',
        'volume': 100,
        'mute': False,
        'device': 'Main',
    }
    kwargs.update(overrides)
    return AppModel(**kwargs)


class TestAppModel(unittest.TestCase):

    def test_icon_defaults_when_missing(self):
        app = _app(icon=None)
        self.assertEqual(app.icon, 'audio-card')

    def test_set_volume(self):
        app = _app()
        app.set_volume(42)
        self.assertEqual(app.volume, 42)

    def test_set_mute(self):
        app = _app()
        app.set_mute(True)
        self.assertTrue(app.mute)

    def test_change_device(self):
        app = _app()
        app.change_device('Headphones')
        self.assertEqual(app.device, 'Headphones')


class TestClassFunctions(unittest.TestCase):

    def test_pa_to_app_model(self):
        pa_app = _FakePaApp(index=5, name='Firefox', values=[0.75], device_name='Main')
        app = AppModel.pa_to_app_model(pa_app, 'sink_input')
        self.assertIsInstance(app, AppModel)
        self.assertEqual(app.index, 5)
        self.assertEqual(app.label, 'Firefox')
        self.assertEqual(app.volume, 75)
        self.assertEqual(app.device, 'Main')

    def test_list_apps(self):
        pa_app_list = [
            _FakePaApp(index=1, name='Firefox', values=[1.0]),
            _FakePaApp(index=2, name='mpv', values=[0.5]),
        ]
        app_list = AppModel.list_apps('sink_input', pa_app_list)
        self.assertIsInstance(app_list, list)
        self.assertEqual(len(app_list), 2)
        self.assertTrue(all(isinstance(app, AppModel) for app in app_list))

    def test_list_apps_empty(self):
        self.assertEqual(AppModel.list_apps('sink_input', []), [])


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
