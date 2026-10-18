import unittest
from unittest import mock

from pulsemeeter.controller.app_controller import AppController
from pulsemeeter.scripts import pmctl


class TestChangeDevice(unittest.TestCase):
    '''A pick in the app dropdown pins or unpins through the metadata, for both stream types.'''

    def setUp(self):
        self.patches = {name: mock.patch.object(pmctl, name).start()
                        for name in ('get_app_object_id', 'pin_app', 'unpin_app')}
        self.addCleanup(mock.patch.stopall)
        self.patches['get_app_object_id'].return_value = 56
        self.controller = AppController()
        self.emitted = []
        self.controller.connect('app_device_change', lambda *args: self.emitted.append(args))

    def test_pick_device_pins(self):
        for app_type, device_type in (('sink_input', 'sink'), ('source_output', 'source')):
            self.patches['pin_app'].reset_mock()
            self.controller.change_device(app_type, 7, 'some_device')
            self.patches['pin_app'].assert_called_once_with(56, device_type, 'some_device')
        self.patches['unpin_app'].assert_not_called()
        assert self.emitted[-1] == ('source_output', 7, 'some_device')

    def test_pick_default_unpins(self):
        self.controller.change_device('sink_input', 7, '')
        self.patches['unpin_app'].assert_called_once_with(56)
        self.patches['pin_app'].assert_not_called()
        assert self.emitted == [('sink_input', 7, '')]

    def test_stream_gone(self):
        self.patches['get_app_object_id'].return_value = None
        self.controller.change_device('sink_input', 7, 'some_device')
        self.patches['pin_app'].assert_not_called()
        assert self.emitted == [('sink_input', 7, 'some_device')]


if __name__ == '__main__':
    unittest.main()
