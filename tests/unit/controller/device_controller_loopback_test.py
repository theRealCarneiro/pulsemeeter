import unittest
from types import SimpleNamespace
from unittest import mock

from pulsemeeter.scripts import pmctl
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.controller.device_controller import DeviceController
from pulsemeeter.repository.device_repository import DeviceRepository


PATCHED = (
    'get_loopback_targets', 'get_node_serial', 'create_loopback', 'destroy_loopback',
    'kill_stray_loopback', 'wait_for_loopback_gone', 'set_route_volume', 'link',
    'create_intermediate_sink', 'wait_for_node', 'remove_intermediate_sink', 'remove_device',
)

MUSIC = SimpleNamespace(name='music', device_type='sink', channels=2, channel_list=['FL', 'FR'])
SPEAKERS = SimpleNamespace(name='speakers', device_type='sink', channels=2, channel_list=['FL', 'FR'])
VIRTUAL_OUT = SimpleNamespace(name='virtual_out', device_type='source', channels=2, channel_list=['FL', 'FR'])
HW_INPUT = SimpleNamespace(name='hw_input', device_type='source', channels=2, channel_list=['FL', 'FR'])

A_ROUTE = pmctl.make_loopback_name('music', 'speakers')
B_ROUTE = pmctl.make_loopback_name('music', 'virtual_out')
BRIDGE = pmctl.make_intermediate_sink_name(B_ROUTE)


class LoopbackConnectionTest(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch.multiple(pmctl, **{name: mock.DEFAULT for name in PATCHED})
        self.pm = SimpleNamespace(**patcher.start())
        self.addCleanup(patcher.stop)
        # don't start the post-create volume thread
        thread_patcher = mock.patch('pulsemeeter.controller.device_controller.threading.Thread')
        thread_patcher.start()
        self.addCleanup(thread_patcher.stop)

        self.pm.get_node_serial.return_value = ''
        self.pm.kill_stray_loopback.return_value = 0
        self.pm.wait_for_loopback_gone.return_value = True

        self.controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(self.controller)
        self.controller._loopback_procs = {}
        self.controller._intermediate_sinks = {}
        self.connection = SimpleNamespace(route_volume=42, connect_failed=False, connect_error='')

    def connect(self, output, state=True):
        name = B_ROUTE if output is VIRTUAL_OUT else A_ROUTE
        self.controller._set_loopback_connection(name, MUSIC, output, self.connection, state)

    def test_current_loopback_is_kept(self):
        self.pm.get_loopback_targets.return_value = ('music', 'speakers')
        self.connect(SPEAKERS)
        self.pm.create_loopback.assert_not_called()
        self.pm.kill_stray_loopback.assert_not_called()
        self.pm.set_route_volume.assert_called_once_with(A_ROUTE, 42)
        assert not self.connection.connect_failed

    def test_serial_targeted_loopback_is_replaced(self):
        # spawned by an older version, pinned to serials
        self.pm.get_loopback_targets.return_value = ('129', '104')
        self.pm.kill_stray_loopback.return_value = 1
        self.connect(SPEAKERS)
        self.pm.kill_stray_loopback.assert_called_once_with(A_ROUTE)
        self.pm.wait_for_loopback_gone.assert_called_once_with(A_ROUTE)
        self.pm.create_loopback.assert_called_once_with(
            name=A_ROUTE, capture_target='music', playback_target='speakers', channels=2, capture_sink=True)
        assert A_ROUTE in self.controller._loopback_procs

    def test_missing_or_duplicated_loopback_is_created(self):
        self.pm.get_loopback_targets.return_value = None
        self.connect(SPEAKERS)
        self.pm.create_loopback.assert_called_once()
        self.pm.wait_for_loopback_gone.assert_not_called()

    def test_turning_off_kills_loopback_we_did_not_spawn(self):
        self.pm.kill_stray_loopback.return_value = 1
        self.connect(SPEAKERS, state=False)
        self.pm.destroy_loopback.assert_not_called()
        self.pm.kill_stray_loopback.assert_called_once_with(A_ROUTE)
        self.pm.wait_for_loopback_gone.assert_called_once_with(A_ROUTE)

    def test_turning_off_destroys_our_own_loopback(self):
        proc = mock.Mock()
        self.controller._loopback_procs[A_ROUTE] = proc
        self.connect(SPEAKERS, state=False)
        self.pm.destroy_loopback.assert_called_once_with(proc)
        self.pm.wait_for_loopback_gone.assert_called_once_with(A_ROUTE)
        assert A_ROUTE not in self.controller._loopback_procs

    def test_hardware_input_is_captured_as_source(self):
        self.pm.get_loopback_targets.return_value = None
        route = pmctl.make_loopback_name('hw_input', 'speakers')
        self.controller._set_loopback_connection(route, HW_INPUT, SPEAKERS, self.connection, True)
        self.pm.create_loopback.assert_called_once_with(
            name=route, capture_target='hw_input', playback_target='speakers', channels=2, capture_sink=False)

    def test_current_b_type_loopback_is_kept_and_bridge_relinked(self):
        self.pm.get_loopback_targets.return_value = ('music', BRIDGE)
        self.pm.get_node_serial.return_value = '158'
        self.connect(VIRTUAL_OUT)
        self.pm.create_loopback.assert_not_called()
        self.pm.link.assert_called_once_with(BRIDGE, 'virtual_out')

    def test_b_type_loopback_without_bridge_is_replaced(self):
        self.pm.get_loopback_targets.return_value = ('music', BRIDGE)
        self.pm.create_intermediate_sink.return_value = BRIDGE
        self.connect(VIRTUAL_OUT)
        self.pm.create_loopback.assert_called_once_with(
            name=B_ROUTE, capture_target='music', playback_target=BRIDGE, channels=2, capture_sink=True)

    def test_b_type_bridge_timeout_fails_route(self):
        self.pm.get_loopback_targets.return_value = None
        self.pm.create_intermediate_sink.return_value = BRIDGE
        self.pm.wait_for_node.return_value = ''
        self.connect(VIRTUAL_OUT)
        self.pm.create_loopback.assert_not_called()
        assert self.connection.connect_failed

    def test_teardown_removes_leftover_bridge(self):
        # bridge left over from a previous run
        self.pm.get_node_serial.return_value = '158'
        self.connect(VIRTUAL_OUT, state=False)
        self.pm.link.assert_called_once_with(BRIDGE, 'virtual_out', state=False)
        self.pm.remove_intermediate_sink.assert_called_once_with(B_ROUTE)

    def test_cleanup_kills_unowned_loopback_before_removing_sink(self):
        music = SimpleNamespace(name='music', device_class='virtual', external=False, connections={'a': {'1': None}})
        speakers = SimpleNamespace(name='speakers', device_type='sink', device_class='hardware', external=False)
        devices = {'vi': {'1': music}, 'hi': {}, 'a': {'1': speakers}, 'b': {}}
        repository = mock.create_autospec(DeviceRepository, instance=True)
        repository.get_devices_by_type.side_effect = devices.get
        repository.get_device.side_effect = lambda device_type, device_id: devices[device_type].get(device_id)
        repository.get_all_devices.return_value = devices
        self.controller.device_repository = repository

        order = mock.Mock()
        order.attach_mock(self.pm.kill_stray_loopback, 'kill_stray_loopback')
        order.attach_mock(self.pm.remove_device, 'remove_device')
        self.controller.cleanup()
        assert order.mock_calls == [mock.call.kill_stray_loopback(A_ROUTE), mock.call.remove_device('music')]
