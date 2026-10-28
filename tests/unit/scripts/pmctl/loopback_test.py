import signal
import unittest
from types import SimpleNamespace
from unittest import mock

from pulsemeeter.scripts import pmctl


NAME = 'pm_route_music_to_speakers'


def _stream(node_name, **props):
    return SimpleNamespace(proplist={'node.name': node_name, **props})


def _loopback(name=NAME, pid=111, capture_target='10', playback_target='20'):
    '''The (sink-input, source-output) pair pipewire-pulse lists for one pw-loopback.'''
    group = f'pw-loopback-{pid}'
    playback = _stream(f'output.{name}', **{'node.group': group, 'pulsemeeter.target': playback_target})
    capture = _stream(f'input.{name}', **{'node.group': group, 'pulsemeeter.target': capture_target})
    return playback, capture


def _pulse(sink_inputs=(), source_outputs=()):
    '''Patch pmctl.PULSE to list the given streams.'''
    pulse = mock.Mock()
    pulse.sink_input_list.return_value = list(sink_inputs)
    pulse.source_output_list.return_value = list(source_outputs)
    return mock.patch.object(pmctl, 'PULSE', pulse)


def _cmdline(argv):
    return mock.mock_open(read_data=b'\0'.join(argv) + b'\0')


class TestCreateLoopback(unittest.TestCase):

    def test_unlinked_streams_record_quoted_targets(self):
        with mock.patch.object(pmctl.subprocess, 'Popen') as m_popen:
            pmctl.create_loopback('pm_route_Virtual_Input_to_speakers', 'Virtual Input', 'speakers', 2)
        command = m_popen.call_args.args[0]
        assert command[command.index('--channel-map') + 1] == '[ AUX0 AUX1 ]'
        assert command[command.index('--capture-props') + 1] == (
            'pulsemeeter.target="Virtual Input" node.autoconnect=false node.linger=true node.virtual=true')
        assert command[command.index('--playback-props') + 1] == (
            'pulsemeeter.target="speakers" node.autoconnect=false node.linger=true node.virtual=true')


class TestLoopbackStreams(unittest.TestCase):

    def test_matches_node_name_exactly(self):
        playback, capture = _loopback()
        other_playback, other_capture = _loopback(name=f'{NAME}.2')
        with _pulse([other_playback, playback], [other_capture, capture]):
            assert pmctl._loopback_streams(NAME) == ([playback], [capture])


class TestGetLoopbackTargets(unittest.TestCase):

    def test_returns_capture_and_playback_targets(self):
        playback, capture = _loopback(capture_target='129', playback_target='104')
        with _pulse([playback], [capture]):
            assert pmctl.get_loopback_targets(NAME) == ('129', '104')

    def test_none_when_not_running(self):
        with _pulse():
            assert pmctl.get_loopback_targets(NAME) is None

    def test_none_when_duplicated(self):
        first, second = _loopback(pid=111), _loopback(pid=222)
        with _pulse([first[0], second[0]], [first[1], second[1]]):
            assert pmctl.get_loopback_targets(NAME) is None


class TestKillStrayLoopback(unittest.TestCase):

    def test_signals_pid_from_node_group_once(self):
        playback, capture = _loopback(pid=111)
        with _pulse([playback], [capture]), \
                mock.patch('builtins.open', _cmdline([b'pw-loopback', b'--name', NAME.encode()])) as m_open, \
                mock.patch.object(pmctl.os, 'kill') as m_kill:
            assert pmctl.kill_stray_loopback(NAME) == 1
        m_open.assert_called_once_with('/proc/111/cmdline', 'rb')
        m_kill.assert_called_once_with(111, signal.SIGTERM)

    def test_skips_reused_pid(self):
        playback, capture = _loopback(pid=111)
        with _pulse([playback], [capture]), \
                mock.patch('builtins.open', _cmdline([b'/usr/bin/bash'])), \
                mock.patch.object(pmctl.os, 'kill') as m_kill:
            assert pmctl.kill_stray_loopback(NAME) == 0
        m_kill.assert_not_called()

    def test_skips_loopback_with_other_name(self):
        playback, capture = _loopback(pid=111)
        with _pulse([playback], [capture]), \
                mock.patch('builtins.open', _cmdline([b'pw-loopback', b'--name', f'{NAME}.2'.encode()])), \
                mock.patch.object(pmctl.os, 'kill') as m_kill:
            assert pmctl.kill_stray_loopback(NAME) == 0
        m_kill.assert_not_called()

    def test_process_already_gone(self):
        playback, capture = _loopback(pid=111)
        with _pulse([playback], [capture]), \
                mock.patch('builtins.open', side_effect=FileNotFoundError), \
                mock.patch.object(pmctl.os, 'kill') as m_kill:
            assert pmctl.kill_stray_loopback(NAME) == 0
        m_kill.assert_not_called()

    def test_ignores_streams_without_loopback_group(self):
        with _pulse([_stream(f'output.{NAME}', **{'node.group': 'something-else'})]), \
                mock.patch.object(pmctl.os, 'kill') as m_kill:
            assert pmctl.kill_stray_loopback(NAME) == 0
        m_kill.assert_not_called()


class TestWaitForLoopbackGone(unittest.TestCase):

    def test_true_when_gone(self):
        with _pulse():
            assert pmctl.wait_for_loopback_gone(NAME, timeout=0.1, interval=0.01) is True

    def test_false_when_still_present(self):
        playback, capture = _loopback()
        with _pulse([playback], [capture]):
            assert pmctl.wait_for_loopback_gone(NAME, timeout=0.05, interval=0.01) is False
