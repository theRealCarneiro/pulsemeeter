import json
import unittest
from unittest import mock

from pulsemeeter.scripts import pmctl


def _dump(graph):
    '''Patch pw-dump to return the given graph, then call get_pinned_app_ids.'''
    with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                    return_value=json.dumps(graph).encode()):
        return pmctl.get_pinned_app_ids()


def _node(node_id, **props):
    return {'id': node_id, 'type': 'PipeWire:Interface:Node',
            'info': {'props': props}}


def _default_metadata(*entries):
    return {'type': 'PipeWire:Interface:Metadata',
            'props': {'metadata.name': 'default'},
            'metadata': list(entries)}


class TestGetPinnedAppIds(unittest.TestCase):

    def test_node_prop_target_is_pinned(self):
        assert _dump([_node(5, **{'target.object': 'somesink'})]) == {5}

    def test_metadata_target_is_pinned(self):
        graph = [_default_metadata({'subject': 7, 'key': 'target.object', 'value': 42})]
        assert _dump(graph) == {7}

    def test_target_node_key_also_counts(self):
        assert _dump([_node(9, **{'target.node': 3})]) == {9}

    def test_empty_or_minus_one_not_pinned(self):
        graph = [
            _node(1, **{'target.object': ''}),
            _node(2, **{'target.object': -1}),
            _node(3, **{'target.node': '-1'}),
            _node(4),  # no target props at all
            _default_metadata({'subject': 5, 'key': 'target.object', 'value': ''}),
        ]
        assert _dump(graph) == set()

    def test_non_default_metadata_ignored(self):
        graph = [{'type': 'PipeWire:Interface:Metadata',
                  'props': {'metadata.name': 'route-settings'},
                  'metadata': [{'subject': 8, 'key': 'target.object', 'value': 1}]}]
        assert _dump(graph) == set()

    def test_mixed_props_and_metadata(self):
        graph = [
            _node(1, **{'target.object': 'x'}),
            _node(2),
            _default_metadata({'subject': 3, 'key': 'target.node', 'value': 10}),
        ]
        assert _dump(graph) == {1, 3}

    def test_pw_dump_missing_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        side_effect=FileNotFoundError()):
            assert pmctl.get_pinned_app_ids() is None

    def test_pw_dump_bad_json_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        return_value=b'not json'):
            assert pmctl.get_pinned_app_ids() is None


if __name__ == '__main__':
    unittest.main()
