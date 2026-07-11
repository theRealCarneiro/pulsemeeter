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
