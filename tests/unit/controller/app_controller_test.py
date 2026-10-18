import unittest
from types import SimpleNamespace
from unittest import mock

import pulsectl
from pulsectl import PulseSinkInputInfo, PulseSourceOutputInfo

from pulsemeeter.scripts import pmctl
from pulsemeeter.model.app_model import AppModel
from pulsemeeter.controller.app_controller import AppController


INDEX = 7
OBJECT_ID = 42
DEVICE = SimpleNamespace(name='test_device')


def _stream(app_type):
    '''A real pulsectl stream object: a sink input has .sink, a source output has .source.'''
    cls = PulseSinkInputInfo if app_type == 'sink_input' else PulseSourceOutputInfo
    fields = dict.fromkeys(cls.c_struct_fields.split(), 0)
    fields.update({'index': INDEX, 'sink' if app_type == 'sink_input' else 'source': 3})
    stream = cls(**fields)
    stream.proplist = {'application.name': 'test_app', 'object.id': str(OBJECT_ID)}
    stream.volume = pulsectl.PulseVolumeInfo(1.0, 2)
    return stream


class _AppControllerCases:
    '''Shared cases; subclasses set the stream type.'''
    APP_TYPE = None

    def setUp(self):
        self.app = _stream(self.APP_TYPE)
        self.pulse = mock.Mock()
        self.pulse.sink_info.return_value = DEVICE
        self.pulse.source_info.return_value = DEVICE
        for app_type in ('sink_input', 'source_output'):
            info = getattr(self.pulse, f'{app_type}_info')
            if app_type == self.APP_TYPE:
                info.return_value = self.app
            else:
                info.side_effect = pulsectl.PulseIndexError(INDEX)

        patcher = mock.patch.multiple(pmctl, PULSE=self.pulse, unpin_app=mock.DEFAULT, move_app_device=mock.DEFAULT)
        self.pm = SimpleNamespace(**patcher.start())
        self.addCleanup(patcher.stop)

        self.controller = AppController()
        self.emitted = []
        for signal_name in ('app_volume', 'app_mute', 'app_device_change'):
            self.controller.connect(signal_name, lambda *args, name=signal_name: self.emitted.append((name, *args)))

    def test_blank_device_unpins_stream(self):
        self.controller.change_device(self.APP_TYPE, INDEX, '')
        self.pm.unpin_app.assert_called_once_with(OBJECT_ID)
        self.pm.move_app_device.assert_not_called()
        assert self.emitted == [('app_device_change', self.APP_TYPE, INDEX, '')]

    def test_blank_device_for_gone_stream_skips_unpin(self):
        getattr(self.pulse, f'{self.APP_TYPE}_info').side_effect = pulsectl.PulseIndexError(INDEX)
        self.controller.change_device(self.APP_TYPE, INDEX, '')
        self.pm.unpin_app.assert_not_called()
        assert self.emitted == [('app_device_change', self.APP_TYPE, INDEX, '')]

    def test_device_name_moves_stream(self):
        self.controller.change_device(self.APP_TYPE, INDEX, 'test_device')
        self.pm.move_app_device.assert_called_once_with(self.APP_TYPE, INDEX, 'test_device')
        self.pm.unpin_app.assert_not_called()
        assert self.emitted == [('app_device_change', self.APP_TYPE, INDEX, 'test_device')]

    def test_set_mute(self):
        self.controller.set_mute(self.APP_TYPE, INDEX, True)
        self.pulse.mute.assert_called_once_with(self.app, True)
        assert self.emitted == [('app_mute', self.APP_TYPE, INDEX, True)]

    def test_set_volume(self):
        self.controller.set_volume(self.APP_TYPE, INDEX, 50)
        app, volume = self.pulse.volume_set.call_args.args
        assert app is self.app
        assert volume.values == [0.5, 0.5]
        assert self.emitted == [('app_volume', self.APP_TYPE, INDEX, 50)]

    def test_get_app_by_id(self):
        # AppModel.get_app_by_id is the same wrapper over pmctl.app_by_id
        for get_app_by_id in (self.controller.get_app_by_id, AppModel.get_app_by_id):
            app_model = get_app_by_id(INDEX, self.APP_TYPE)
            assert app_model.app_type == self.APP_TYPE
            assert app_model.index == INDEX
            assert app_model.device == 'test_device'
            assert app_model.object_id == OBJECT_ID


class TestSinkInput(_AppControllerCases, unittest.TestCase):
    APP_TYPE = 'sink_input'


class TestSourceOutput(_AppControllerCases, unittest.TestCase):
    APP_TYPE = 'source_output'


if __name__ == '__main__':
    unittest.main()
