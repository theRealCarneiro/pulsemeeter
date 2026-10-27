import unittest
from unittest import mock

from pulsemeeter.scripts import pmctl
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.repository.device_repository import DeviceRepository
from pulsemeeter.controller.device_controller import DeviceController


def _device(name, device_type='sink', device_class='virtual'):
    # Every device is configured stereo: the tests vary what PipeWire reports
    return DeviceModel(
        name=name, device_type=device_type, device_class=device_class, primary=False,
        channels=2, channel_list=['FL', 'FR'], selected_channels=[True, True],
    )


class LinkConnectionTest(unittest.TestCase):

    def setUp(self):
        self.ports = {}
        get_ports = mock.patch.object(pmctl, 'get_ports', side_effect=lambda _t, name: self.ports[name])
        link = mock.patch.object(pmctl, 'link', return_value=True)
        get_ports.start()
        self.link = link.start()
        self.addCleanup(mock.patch.stopall)

        self.controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(self.controller)
        self.connection = ConnectionModel(nick='out', input_sel_channels=[True, True], output_sel_channels=[True, True])

    def connect(self, input_ports, output_ports, state=True):
        self.ports = {'music': input_ports, 'headset': output_ports}
        self.controller._set_link_connection(
            _device('music'), _device('headset', device_class='hardware'), self.connection, state
        )
        return [call.args for call in self.link.call_args_list]

    def test_headset_dropped_to_mono_gets_both_channels(self):
        # The config still says stereo; PipeWire says the headset is now mono
        assert self.connect(['monitor_FL', 'monitor_FR'], ['playback_MONO']) == [
            ('music:monitor_FL', 'headset:playback_MONO'),
            ('music:monitor_FR', 'headset:playback_MONO'),
        ]
        assert not self.connection.connect_failed

    def test_port_that_lost_its_position_is_not_cross_wired(self):
        # capture_1 has no speaker position, so only FR is linked, to FR
        assert self.connect(['monitor_FR', 'capture_1'], ['playback_FL', 'playback_FR']) == [
            ('music:monitor_FR', 'headset:playback_FR'),
        ]
        assert self.connection.warning_text() == '1 not routed'
        assert not self.connection.connect_failed

    def test_surround_into_stereo_warns_about_the_dropped_channels(self):
        surround = ['monitor_FC', 'monitor_FL', 'monitor_FR', 'monitor_LFE', 'monitor_RL', 'monitor_RR']
        assert len(self.connect(surround, ['playback_FL', 'playback_FR'])) == 2
        assert self.connection.warning_text() == 'FC, LFE, RL, RR not routed'

    def test_stereo_into_surround_does_not_warn(self):
        # Centre and rears stay silent, but nothing being sent is lost
        surround = ['playback_FC', 'playback_FL', 'playback_FR', 'playback_LFE', 'playback_RL', 'playback_RR']
        assert len(self.connect(['monitor_FL', 'monitor_FR'], surround)) == 2
        assert self.connection.warning_text() == ''

    def test_pair_pw_link_rejects_warns(self):
        self.link.side_effect = [True, False]
        self.connect(['monitor_FL', 'monitor_FR'], ['playback_FL', 'playback_FR'])
        assert self.connection.warning_text() == 'Failed to link: monitor_FR -> playback_FR'
        assert not self.connection.connect_failed

    def test_manual_map_that_lost_an_output_channel_warns(self):
        self.connection.auto_ports = False
        self.connection.port_map = [[0], [1]]
        assert self.connect(['monitor_FL', 'monitor_FR'], ['playback_MONO']) == [
            ('music:monitor_FL', 'headset:playback_MONO'),
        ]
        assert self.connection.warning_text() == 'Links to missing channels in the manual map: 1'

    def test_output_with_a_deselected_channel_does_not_warn(self):
        # A left only virtual mic takes the whole stereo source on its one channel
        self.ports = {'music': ['monitor_FL', 'monitor_FR'], 'mic': ['input_FL', 'input_FR']}
        mic = _device('mic', device_type='source')
        mic.selected_channels = [True, False]
        self.controller._set_link_connection(_device('music'), mic, self.connection, True)
        assert [call.args for call in self.link.call_args_list] == [
            ('music:monitor_FL', 'mic:input_FL'),
            ('music:monitor_FR', 'mic:input_FL'),
        ]
        assert self.connection.warning_text() == ''

    def test_surround_sink_without_lfe_selected_does_not_warn(self):
        surround = ['FC', 'FL', 'FR', 'LFE', 'RL', 'RR']
        self.ports = {'music': [f'monitor_{p}' for p in surround], 'speakers': [f'playback_{p}' for p in surround]}
        speakers = _device('speakers', device_class='hardware')
        speakers.selected_channels = [True, True, True, False, True, True]
        self.controller._set_link_connection(_device('music'), speakers, self.connection, True)
        assert len(self.link.call_args_list) == 5
        assert self.connection.warning_text() == ''

    def test_loopback_connect_clears_a_stale_link_warning(self):
        self.connection.unrouted_ports = ['monitor_FC']
        self.connection.use_loopback = True
        music, headset = _device('music'), _device('headset', device_class='hardware')
        music.connections = {'a': {'1': self.connection}, 'b': {}}
        repository = mock.Mock()
        repository.get_device.side_effect = lambda device_type, _id: music if device_type == 'vi' else headset
        self.controller.device_repository = repository
        with (
            mock.patch.object(self.controller, '_device_available', return_value=True),
            mock.patch.object(self.controller, '_set_loopback_connection'),
        ):
            self.controller.set_connection('vi', '1', 'a', '1', True, soft=True)
        assert self.connection.warning_text() == ''

    def test_stereo_to_a_bigger_pro_audio_interface_pairs_by_order(self):
        assert self.connect(['monitor_FL', 'monitor_FR'], ['playback_AUX0', 'playback_AUX1', 'playback_AUX2']) == [
            ('music:monitor_FL', 'headset:playback_AUX0'),
            ('music:monitor_FR', 'headset:playback_AUX1'),
        ]
        assert not self.connection.connect_failed
        assert self.connection.warning_text() == ''
        assert self.connection.order_pairs == ['monitor_FL -> playback_AUX0', 'monitor_FR -> playback_AUX1']

    def test_manual_map_whose_input_channels_are_gone_fails_the_route(self):
        # Only the second input row is mapped, and the input is down to one port
        self.connection.auto_ports = False
        self.connection.port_map = [[], [0]]
        assert self.connect(['monitor_MONO'], ['playback_FL', 'playback_FR']) == []
        assert self.connection.connect_failed
        assert self.connection.error_text() == 'Every channel the manual map links is missing'


class UpdateConnectionTest(unittest.TestCase):
    '''Port setting edits relink only the pairs that change'''

    def setUp(self):
        self.ports = {'music': ['monitor_FL', 'monitor_FR'], 'headset': ['playback_FL', 'playback_FR']}
        get_ports = mock.patch.object(pmctl, 'get_ports', side_effect=lambda _t, name: self.ports[name])
        link = mock.patch.object(pmctl, 'link', return_value=True)
        get_ports.start()
        self.link = link.start()
        self.addCleanup(mock.patch.stopall)

        self.music = _device('music')
        self.headset = _device('headset', device_class='hardware')
        self.connection = ConnectionModel(
            nick='out', state=True, input_sel_channels=[True, True], output_sel_channels=[True, True]
        )
        self.music.connections = {'a': {'1': self.connection}, 'b': {}}

        repository = mock.Mock()
        repository.get_device.side_effect = lambda device_type, _id: self.music if device_type == 'vi' else self.headset
        self.controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(self.controller)
        self.controller.device_repository = repository

    def edit(self, auto_ports, port_map):
        edited = self.connection.model_copy(deep=True)
        edited.auto_ports = auto_ports
        edited.port_map = port_map
        self.controller.update_connection('vi', '1', 'a', '1', edited)
        return [(call.args, call.kwargs['state']) for call in self.link.call_args_list]

    def test_manual_change_unlinks_only_the_removed_pair(self):
        # Auto links FL to FL and FR to FR, the edit sends both to FL
        assert self.edit(False, [[0], [0]]) == [
            (('music:monitor_FR', 'headset:playback_FR'), False),
            (('music:monitor_FL', 'headset:playback_FL'), True),
            (('music:monitor_FR', 'headset:playback_FL'), True),
        ]

    def test_going_manual_with_the_auto_pairs_unlinks_nothing(self):
        # Surround into stereo warns until the user takes the routing as their own
        self.ports['music'] = ['monitor_FC', 'monitor_FL', 'monitor_FR', 'monitor_LFE']
        self.controller._set_link_connection(self.music, self.headset, self.connection, True)
        assert self.connection.unrouted_ports == ['monitor_FC', 'monitor_LFE']
        self.link.reset_mock()

        calls = self.edit(False, [[], [0], [1], []])
        assert all(state for _args, state in calls)
        assert self.connection.warning_text() == ''
        assert self.connection.unrouted_ports == []

    def test_back_to_auto_keeps_the_manual_map(self):
        self.connection.auto_ports = False
        self.connection.port_map = [[0], [0]]
        self.edit(True, [[0], [0]])
        assert self.connection.auto_ports
        assert self.connection.port_map == [[0], [0]]

    def test_edit_while_a_device_has_no_ports_only_saves(self):
        self.connection.order_pairs = ['monitor_FL -> playback_AUX0']
        self.ports['headset'] = []
        assert self.edit(False, [[0], [1]]) == []
        assert self.connection.port_map == [[0], [1]]
        assert self.connection.order_pairs == []
        assert not self.connection.connect_failed


class StartupTest(unittest.TestCase):
    '''Startup links a new virtual device once all its ports are listed'''

    def setUp(self):
        self.polls = 0
        self.existing = {'headphones'}
        for name, kwargs in (
            ('is_pipewire', {'return_value': True}),
            ('device_exists', {'side_effect': lambda name: name in self.existing}),
            ('create_device', {'side_effect': lambda _type, name, *_args: self.existing.add(name)}),
            ('list_ports', {'side_effect': self.list_ports}),
            ('kill_stray_loopback', {'return_value': 0}),
        ):
            mock.patch.object(pmctl, name, **kwargs).start()
        mock.patch('pulsemeeter.scripts.pmctl.time.sleep', side_effect=self.next_poll).start()
        self.link = mock.patch.object(pmctl, 'link', return_value=True).start()
        self.addCleanup(mock.patch.stopall)

    def next_poll(self, _seconds):
        self.polls += 1

    def list_ports(self, port_type):
        # The new sink has no ports at first, then only its right channel, then both
        positions = [[], ['FR'], ['FL', 'FR']][min(self.polls, 2)]
        prefix = 'playback' if port_type == 'input' else 'monitor'
        ports = {'desktop': [f'{prefix}_{position}' for position in positions]}
        if port_type == 'input':
            ports['headphones'] = ['playback_FL', 'playback_FR']
        return ports

    def test_new_sink_is_linked_once_all_its_ports_are_listed(self):
        config = ConfigModel(devices={'vi': {'1': _device('desktop')}, 'a': {'1': _device('headphones', device_class='hardware')}})
        config.devices['vi']['1'].connections['a']['1'].state = True

        DeviceController(DeviceRepository(mock.Mock(get_config=lambda: config)))

        assert [call.args for call in self.link.call_args_list] == [
            ('desktop:monitor_FL', 'headphones:playback_FL'),
            ('desktop:monitor_FR', 'headphones:playback_FR'),
        ]
