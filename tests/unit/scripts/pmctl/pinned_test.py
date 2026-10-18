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

    def test_dumps_only_the_default_metadata(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output', return_value=b'[]') as check_output:
            assert pmctl.get_pinned_app_ids() == set()
        assert check_output.call_args.args[0] == ['pw-dump', 'default']

    def test_metadata_target_is_pinned(self):
        graph = [_default_metadata({'subject': 7, 'key': 'target.object', 'value': 42})]
        assert _dump(graph) == {7}

    def test_target_node_key_also_counts(self):
        assert _dump([_default_metadata({'subject': 9, 'key': 'target.node', 'value': 3})]) == {9}

    def test_empty_or_minus_one_not_pinned(self):
        graph = [_default_metadata(
            {'subject': 1, 'key': 'target.object', 'value': ''},
            {'subject': 2, 'key': 'target.object', 'value': -1},
            {'subject': 3, 'key': 'target.node', 'value': '-1'},
        )]
        assert _dump(graph) == set()

    def test_non_default_metadata_ignored(self):
        graph = [{'type': 'PipeWire:Interface:Metadata',
                  'props': {'metadata.name': 'route-settings'},
                  'metadata': [{'subject': 8, 'key': 'target.object', 'value': 1}]}]
        assert _dump(graph) == set()

    def test_nodes_ignored(self):
        # pw-dump also matches a node named "default"; node targets come from has_target()
        graph = [_node(1, **{'target.object': 'x'}),
                 _default_metadata({'subject': 3, 'key': 'target.node', 'value': 10})]
        assert _dump(graph) == {3}

    def test_pw_dump_missing_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        side_effect=FileNotFoundError()):
            assert pmctl.get_pinned_app_ids() is None

    def test_pw_dump_bad_json_returns_none(self):
        with mock.patch('pulsemeeter.scripts.pmctl.subprocess.check_output',
                        return_value=b'not json'):
            assert pmctl.get_pinned_app_ids() is None


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


if __name__ == '__main__':
    unittest.main()
