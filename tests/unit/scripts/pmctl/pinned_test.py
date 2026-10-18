import json
import unittest
from types import SimpleNamespace
from unittest import mock

from pulsemeeter.scripts import pmctl


def _dump(graph):
    '''Patch pw-dump to return the given graph, then call get_app_pins.'''
    with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                    return_value=json.dumps(graph).encode()):
        return pmctl.get_app_pins()


def _node(node_id, **props):
    return {'id': node_id, 'type': 'PipeWire:Interface:Node',
            'info': {'props': props}}


def _default_metadata(*entries):
    return {'type': 'PipeWire:Interface:Metadata',
            'props': {'metadata.name': 'default'},
            'metadata': list(entries)}


def _target(subject, key, value):
    return {'subject': subject, 'key': key, 'type': 'Spa:Id', 'value': value}


class TestGetAppPins(unittest.TestCase):

    def test_dumps_only_the_default_metadata(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output', return_value=b'[]') as check_output:
            assert pmctl.get_app_pins() == {}
        assert check_output.call_args.args[0] == ['pw-dump', 'default']

    def test_target_is_pinned(self):
        graph = [_default_metadata(_target(7, 'target.object', 42), _target(7, 'target.node', 31))]
        assert _dump(graph) == {7: True}

    def test_one_key_is_enough(self):
        assert _dump([_default_metadata(_target(9, 'target.node', 3))]) == {9: True}
        assert _dump([_default_metadata(_target(9, 'target.object', 'some_sink'))]) == {9: True}

    def test_minus_one_follows_the_default(self):
        graph = [_default_metadata(_target(1, 'target.node', -1), _target(1, 'target.object', '-1'))]
        assert _dump(graph) == {1: False}

    def test_empty_value_is_no_entry(self):
        # what older pulsemeeter versions left behind on unpin
        assert _dump([_default_metadata(_target(5, 'target.object', ''))]) == {}

    def test_other_keys_and_metadata_ignored(self):
        graph = [
            _default_metadata({'subject': 0, 'key': 'default.audio.sink', 'value': {'name': 'x'}}),
            {'type': 'PipeWire:Interface:Metadata', 'props': {'metadata.name': 'route-settings'},
             'metadata': [_target(8, 'target.object', 1)]},
        ]
        assert _dump(graph) == {}

    def test_nodes_ignored(self):
        # pw-dump also matches a node named "default"; node targets come from has_target()
        graph = [_node(1, **{'target.object': 'x'}), _default_metadata(_target(3, 'target.node', 10))]
        assert _dump(graph) == {3: True}

    def test_pw_dump_missing_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        side_effect=FileNotFoundError()):
            assert pmctl.get_app_pins() is None

    def test_pw_dump_bad_json_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        return_value=b'not json'):
            assert pmctl.get_app_pins() is None


class TestHasTarget(unittest.TestCase):

    def test_target_object(self):
        assert pmctl.has_target({'target.object': 'somesink'})

    def test_target_node_and_legacy_node_target(self):
        assert pmctl.has_target({'target.node': '3'})
        assert pmctl.has_target({'node.target': '3'})

    def test_empty_or_minus_one(self):
        assert not pmctl.has_target({'target.object': ''})
        assert not pmctl.has_target({'target.object': -1})
        assert not pmctl.has_target({'target.node': '-1'})

    def test_no_target(self):
        assert not pmctl.has_target({'application.name': 'app'})


class TestIsMovable(unittest.TestCase):

    def test_plain_stream(self):
        assert pmctl.is_movable({'application.name': 'app'})

    def test_dont_move(self):
        assert not pmctl.is_movable({'node.dont-move': 'true'})

    def test_dont_reconnect(self):
        # pipewire-pulse's form of PA_STREAM_DONT_MOVE
        assert not pmctl.is_movable({'node.dont-reconnect': 'true'})
        assert not pmctl.is_movable({'node.dont-reconnect': '1'})

    def test_false_values(self):
        assert pmctl.is_movable({'node.dont-move': 'false', 'node.dont-reconnect': '0'})


class TestPinApp(unittest.TestCase):

    def setUp(self):
        run = mock.patch('pulsemeeter.scripts.pmctl.subprocess.run')
        self.run = run.start()
        self.addCleanup(run.stop)

    def _commands(self):
        return [c.args[0] for c in self.run.call_args_list]

    def test_pin_writes_node_id_and_serial(self):
        device = SimpleNamespace(index=57, proplist={'object.id': '49', 'object.serial': '57'})
        with mock.patch.object(pmctl, 'get_device_by_name', return_value=device) as lookup:
            assert pmctl.pin_app(56, 'sink', 'test_sink_b')
        lookup.assert_called_once_with('sink', 'test_sink_b')
        assert self._commands() == [
            ['pw-metadata', '--', '56', 'target.node', '49', 'Spa:Id'],
            ['pw-metadata', '--', '56', 'target.object', '57', 'Spa:Id'],
        ]

    def test_pin_to_missing_device_writes_nothing(self):
        with mock.patch.object(pmctl, 'get_device_by_name', return_value=None):
            assert not pmctl.pin_app(56, 'source', 'gone')
        assert self._commands() == []

    def test_unpin_writes_follow_default(self):
        assert pmctl.unpin_app(56)
        assert self._commands() == [
            ['pw-metadata', '--', '56', 'target.node', '-1', 'Spa:Id'],
            ['pw-metadata', '--', '56', 'target.object', '-1', 'Spa:Id'],
        ]

    def test_pw_metadata_missing(self):
        self.run.side_effect = FileNotFoundError()
        assert not pmctl.unpin_app(56)


if __name__ == '__main__':
    unittest.main()
