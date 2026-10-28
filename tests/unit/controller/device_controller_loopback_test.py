import unittest
from types import SimpleNamespace
from unittest import mock

from pulsemeeter.scripts import pmctl
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.controller.device_controller import DeviceController
from pulsemeeter.repository.device_repository import DeviceRepository


PATCHED = (
    'get_loopback_targets', 'create_loopback', 'destroy_loopback', 'wait_for_loopback', 'kill_stray_loopback',
    'wait_for_loopback_gone', 'remove_bridge', 'set_route_volume', 'get_links', 'remove_device',
)

ROUTE = pmctl.make_loopback_name('music', 'headset')
CAPTURE, PLAYBACK = pmctl.loopback_nodes(ROUTE)


def _device(name, device_class='virtual'):
    return DeviceModel(
        name=name, device_type='sink', device_class=device_class, primary=False,
        channels=2, channel_list=['FL', 'FR'], selected_channels=[True, True],
    )


class LoopbackConnectionTest(unittest.TestCase):

    def setUp(self):
        self.pm = SimpleNamespace(**mock.patch.multiple(pmctl, **{name: mock.DEFAULT for name in PATCHED}).start())
        self.ports = {'music': ['monitor_FL', 'monitor_FR'], 'headset': ['playback_FL', 'playback_FR']}
        mock.patch.object(pmctl, 'get_ports', side_effect=lambda _type, name: self.ports.get(name, [])).start()
        self.link = mock.patch.object(pmctl, 'link', return_value=True).start()
        self.addCleanup(mock.patch.stopall)

        self.pm.get_loopback_targets.return_value = None
        self.pm.create_loopback.side_effect = self.start_loopback
        self.pm.wait_for_loopback.return_value = True
        self.pm.kill_stray_loopback.return_value = 0
        self.pm.wait_for_loopback_gone.return_value = True
        self.pm.get_links.return_value = []

        self.music = _device('music')
        self.headset = _device('headset', device_class='hardware')
        self.connection = ConnectionModel(
            nick='headset', state=True, use_loopback=True, route_volume=42,
            input_sel_channels=[True, True], output_sel_channels=[True, True],
        )
        self.music.connections = {'a': {'1': self.connection}, 'b': {}}

        repository = mock.Mock()
        repository.get_device.side_effect = lambda device_type, _id: self.music if device_type == 'vi' else self.headset
        self.controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(self.controller)
        self.controller.device_repository = repository
        self.controller._loopback_procs = {}

    def start_loopback(self, name, _capture_target, _playback_target, channels):
        capture, playback = pmctl.loopback_nodes(name)
        self.ports[capture] = [f'input_AUX{index}' for index in range(channels)]
        self.ports[playback] = [f'output_AUX{index}' for index in range(channels)]
        return mock.Mock()

    def connect(self, state=True):
        self.controller._set_loopback_connection(ROUTE, self.music, self.headset, self.connection, state)
        return [call.args for call in self.link.call_args_list]

    def test_port_map_routes_the_loopback(self):
        # Both channels to the left speaker
        self.connection.auto_ports = False
        self.connection.port_map = [[0], [0]]
        calls = mock.Mock()
        calls.attach_mock(self.pm.set_route_volume, 'set_route_volume')
        calls.attach_mock(self.link, 'link')

        assert self.connect() == [
            ('music:monitor_FL', f'{CAPTURE}:input_AUX0'),
            ('music:monitor_FR', f'{CAPTURE}:input_AUX1'),
            (f'{PLAYBACK}:output_AUX0', 'headset:playback_FL'),
            (f'{PLAYBACK}:output_AUX1', 'headset:playback_FL'),
        ]
        self.pm.create_loopback.assert_called_once_with(ROUTE, 'music', 'headset', 2)
        # nothing plays before the route volume is set
        assert calls.mock_calls[0] == mock.call.set_route_volume(ROUTE, 42)
        assert not self.connection.connect_failed

    def test_editing_the_map_relinks_only_the_changed_loopback_pairs(self):
        self.connect()
        self.link.reset_mock()

        edited = self.connection.model_copy(deep=True)
        edited.auto_ports = False
        edited.port_map = [[0], [0]]
        self.controller.update_connection('vi', '1', 'a', '1', edited)

        assert [(call.args, call.kwargs['state']) for call in self.link.call_args_list] == [
            ((f'{PLAYBACK}:output_AUX1', 'headset:playback_FR'), False),
            ((f'{PLAYBACK}:output_AUX0', 'headset:playback_FL'), True),
            ((f'{PLAYBACK}:output_AUX1', 'headset:playback_FL'), True),
        ]

    def test_running_loopback_is_kept_and_relinked_to_the_current_map(self):
        # Left running by an earlier run, whose map swapped the channels
        self.start_loopback(ROUTE, 'music', 'headset', 2)
        self.pm.get_loopback_targets.return_value = ('music', 'headset')
        self.pm.get_links.return_value = [
            (f'{PLAYBACK}:output_AUX0', 'headset:playback_FR'),
            (f'{PLAYBACK}:output_AUX1', 'headset:playback_FR'),
        ]
        self.connect()

        self.pm.create_loopback.assert_not_called()
        self.pm.kill_stray_loopback.assert_not_called()
        assert [call for call in self.link.call_args_list if not call.kwargs['state']] == [
            mock.call(f'{PLAYBACK}:output_AUX0', 'headset:playback_FR', state=False),
        ]
        assert mock.call(f'{PLAYBACK}:output_AUX0', 'headset:playback_FL', state=True) in self.link.call_args_list

    def test_loopback_made_for_something_else_is_replaced(self):
        for case, targets, channels in (
            ('older version, linked by the session manager', ('', ''), 2),
            ('input since changed its channel count', ('music', 'headset'), 1),
        ):
            with self.subTest(case):
                self.pm.create_loopback.reset_mock()
                self.start_loopback(ROUTE, 'music', 'headset', channels)
                self.pm.get_loopback_targets.return_value = targets
                self.pm.kill_stray_loopback.return_value = 1
                self.connect()
                self.pm.kill_stray_loopback.assert_called_with(ROUTE)
                self.pm.remove_bridge.assert_called_with(ROUTE)
                self.pm.create_loopback.assert_called_once_with(ROUTE, 'music', 'headset', 2)

    def test_loopback_that_does_not_start_fails_the_route(self):
        self.pm.wait_for_loopback.return_value = False
        assert self.connect() == []
        assert self.connection.connect_failed

    def test_turning_off_kills_loopback_we_did_not_spawn(self):
        self.pm.kill_stray_loopback.return_value = 1
        self.connect(state=False)
        self.pm.destroy_loopback.assert_not_called()
        self.pm.kill_stray_loopback.assert_called_once_with(ROUTE)
        self.pm.wait_for_loopback_gone.assert_called_once_with(ROUTE)

    def test_turning_off_destroys_our_own_loopback(self):
        proc = mock.Mock()
        self.controller._loopback_procs[ROUTE] = proc
        self.connect(state=False)
        self.pm.destroy_loopback.assert_called_once_with(proc)
        self.pm.wait_for_loopback_gone.assert_called_once_with(ROUTE)
        assert ROUTE not in self.controller._loopback_procs

    def test_cleanup_kills_unowned_loopback_before_removing_sink(self):
        music = SimpleNamespace(name='music', device_class='virtual', external=False, connections={'a': {'1': None}})
        headset = SimpleNamespace(name='headset', device_type='sink', device_class='hardware', external=False)
        devices = {'vi': {'1': music}, 'hi': {}, 'a': {'1': headset}, 'b': {}}
        repository = mock.create_autospec(DeviceRepository, instance=True)
        repository.get_devices_by_type.side_effect = devices.get
        repository.get_device.side_effect = lambda device_type, device_id: devices[device_type].get(device_id)
        repository.get_all_devices.return_value = devices
        self.controller.device_repository = repository

        order = mock.Mock()
        order.attach_mock(self.pm.kill_stray_loopback, 'kill_stray_loopback')
        order.attach_mock(self.pm.remove_device, 'remove_device')
        self.controller.cleanup()
        assert order.mock_calls == [mock.call.kill_stray_loopback(ROUTE), mock.call.remove_device('music')]
