import unittest
from unittest.mock import patch

from pulsemeeter.scripts import pmctl


PW_CLI_INFO_OUTPUT = (
    '\tid: 55\n'
    '\tpermissions: rwxm-\n'
    '\ttype: PipeWire:Interface:Node/3\n'
    '\tinfo:\n'
    '\t\tprops:\n'
    '*\t\tobject.serial = "1264"\n'
    '*\t\tnode.name = "pm_route_test_bridge"\n'
    '*\t\tmedia.class = "Audio/Sink/Internal"\n'
)


class TestGetNodeSerial(unittest.TestCase):

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, PW_CLI_INFO_OUTPUT, ''))
    def test_serial_found(self, mock_run):
        assert pmctl.get_node_serial('pm_route_test_bridge') == '1264'
        mock_run.assert_called_once_with(['pw-cli', 'info', 'pm_route_test_bridge'], split=False)

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, '', 'Error: "info: unknown global \'missing\'"'))
    def test_node_not_found(self, mock_run):
        assert pmctl.get_node_serial('missing') == ''

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(1, '', ''))
    def test_command_failed(self, mock_run):
        assert pmctl.get_node_serial('whatever') == ''

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, 'id: 55\nnode.name = "x"\n', ''))
    def test_output_without_serial(self, mock_run):
        assert pmctl.get_node_serial('x') == ''


PW_LINK_OUTPUT = (
    'my_device:playback_FL\n'
    'my_device:playback_FR\n'
    'other_device:playback_FL\n'
)


class TestGetPorts(unittest.TestCase):

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, PW_LINK_OUTPUT, ''))
    def test_ports_filtered_by_device(self, mock_run):
        assert pmctl.get_ports('output', 'my_device') == ['playback_FL', 'playback_FR']
        mock_run.assert_called_once_with(['pw-link', '--output'])

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, PW_LINK_OUTPUT, ''))
    def test_input_port_type(self, mock_run):
        pmctl.get_ports('input', 'my_device')
        mock_run.assert_called_once_with(['pw-link', '--input'])

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, '', ''))
    def test_no_ports(self, _mock_run):
        assert pmctl.get_ports('output', 'my_device') == []

    @patch('pulsemeeter.scripts.pmctl.run_command', return_value=(1, '', 'boom'))
    def test_command_failure_raises(self, _mock_run):
        with self.assertRaises(RuntimeError):
            pmctl.get_ports('output', 'my_device')


class TestCreateDeviceMediaClass(unittest.TestCase):

    def _create(self, device_type, hidden):
        with patch('pulsemeeter.scripts.pmctl.run_command', return_value=(0, '', '')) as mock_run:
            pmctl.create_device(device_type, 'test_device', 2, ['FL', 'FR'], hidden=hidden)
        return mock_run.call_args[0][0][3]

    def test_sink(self):
        assert 'media.class=Audio/Sink\n' in self._create('sink', False)

    def test_hidden_sink(self):
        assert 'media.class=Audio/Sink/Internal\n' in self._create('sink', True)

    def test_source(self):
        assert 'media.class=Audio/Source/Virtual\n' in self._create('source', False)


class TestLinkChannels(unittest.TestCase):

    def _link_calls(self, input_ports, output_ports, channel_map, state=True):
        ports = {'output': input_ports, 'input': output_ports}
        with (
            patch('pulsemeeter.scripts.pmctl.get_ports', side_effect=lambda t, _n: ports[t]),
            patch('pulsemeeter.scripts.pmctl.link', return_value=True) as mock_link,
        ):
            pmctl.link_channels('in_device', 'out_device', channel_map, state)
        return [call.args for call in mock_link.call_args_list]

    def test_all_pairs_in_range(self):
        calls = self._link_calls(['out_FL', 'out_FR'], ['in_FL', 'in_FR'], '0:0 1:1')
        assert calls == [
            ('in_device:out_FL', 'out_device:in_FL'),
            ('in_device:out_FR', 'out_device:in_FR'),
        ]

    def test_stereo_to_mono_output_links_available_channel(self):
        calls = self._link_calls(['out_FL', 'out_FR'], ['playback_MONO'], '0:0 1:1')
        assert calls == [('in_device:out_FL', 'out_device:playback_MONO')]

    def test_mono_input_to_stereo_output(self):
        calls = self._link_calls(['capture_MONO'], ['in_FL', 'in_FR'], '0:0 1:1')
        assert calls == [('in_device:capture_MONO', 'out_device:in_FL')]

    def test_negative_index_is_skipped(self):
        calls = self._link_calls(['out_FL', 'out_FR'], ['in_FL', 'in_FR'], '0:0 1:-1')
        assert calls == [('in_device:out_FL', 'out_device:in_FL')]

    def test_no_mappable_pair_raises(self):
        with self.assertRaises(RuntimeError):
            self._link_calls(['out_FL', 'out_FR'], ['playback_MONO'], '1:1')

    def test_no_mappable_pair_on_unlink_is_silent(self):
        assert self._link_calls(['out_FL', 'out_FR'], ['playback_MONO'], '1:1', state=False) == []
