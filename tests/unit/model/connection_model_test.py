from pulsemeeter.model.connection_model import ConnectionModel

STEREO_CAPTURE = ['capture_FL', 'capture_FR']
STEREO_PLAYBACK = ['playback_FL', 'playback_FR']
MONO_PLAYBACK = ['playback_MONO']


def _connection(auto_ports=True, port_map=None):
    return ConnectionModel(
        nick='out',
        auto_ports=auto_ports,
        input_sel_channels=[True, True],
        output_sel_channels=[True, True],
        port_map=port_map or [],
    )


class TestRoutingGridAutoPorts:

    def test_stereo_to_stereo(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, STEREO_PLAYBACK, [0, 1], [0, 1]
        )
        assert rows == [(0, 'capture_FL'), (1, 'capture_FR')]
        assert cols == [(0, 'playback_FL'), (1, 'playback_FR')]
        assert checked == {(0, 0), (1, 1)}

    def test_stereo_to_mono_output_is_2x1(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, [0, 1], [0, 1]
        )
        assert len(rows) == 2
        assert len(cols) == 1
        assert checked == {(0, 0)}

    def test_mono_input_to_stereo_output_is_1x2(self):
        rows, cols, checked = _connection().routing_grid(
            ['capture_MONO'], STEREO_PLAYBACK, [0, 1], [0, 1]
        )
        assert rows == [(0, 'capture_MONO')]
        assert len(cols) == 2
        assert checked == {(0, 0)}

    def test_deselected_input_channel_keeps_its_own_port_name(self):
        # Channel 0 unchecked: the single row is channel 1, so it must be labelled with channel 1's port
        rows, _cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, STEREO_PLAYBACK, [1], [0, 1]
        )
        assert rows == [(0, 'capture_FR')]
        # One input against two outputs: pair_match fans out, so the channel feeds both columns
        assert checked == {(0, 0), (0, 1)}

    def test_output_device_gone(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, [], [0, 1], [0, 1]
        )
        assert len(rows) == 2
        assert cols == []
        assert checked == set()


class TestRoutingGridManualPorts:

    def test_target_without_a_port_is_dropped(self):
        rows, cols, checked = _connection(auto_ports=False, port_map=[[1]]).routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, [0, 1], [0, 1]
        )
        assert len(rows) == 2
        assert len(cols) == 1
        assert checked == set()

    def test_downmix_map_is_kept(self):
        _rows, _cols, checked = _connection(auto_ports=False, port_map=[[0], [0]]).routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, [0, 1], [0, 1]
        )
        assert checked == {(0, 0), (1, 0)}

    def test_position_without_a_live_input_port_is_ignored(self):
        _rows, _cols, checked = _connection(auto_ports=False, port_map=[[0], [1]]).routing_grid(
            ['capture_MONO'], STEREO_PLAYBACK, [0, 1], [0, 1]
        )
        assert checked == {(0, 0)}

    def test_map_longer_than_the_channel_list(self):
        _rows, _cols, checked = _connection(auto_ports=False, port_map=[[0], [1], [0], [1]]).routing_grid(
            STEREO_CAPTURE, STEREO_PLAYBACK, [0, 1], [0, 1]
        )
        assert checked == {(0, 0), (1, 1)}


class TestMergePortMap:

    def test_rendered_rows_are_replaced(self):
        connection = _connection(auto_ports=False, port_map=[[0], [1]])
        assert connection.merge_port_map([(0, 1), (1, 0)], [0, 1], 2) == [[1], [0]]

    def test_cleared_row_becomes_empty(self):
        connection = _connection(auto_ports=False, port_map=[[0], [1]])
        assert connection.merge_port_map([(0, 0)], [0, 1], 2) == [[0], []]

    def test_unrendered_row_keeps_its_entries(self):
        connection = _connection(auto_ports=False, port_map=[[0], [1]])
        assert connection.merge_port_map([(0, 0)], [0], 2) == [[0], [1]]

    def test_map_is_sized_to_the_channel_count(self):
        connection = _connection(auto_ports=False, port_map=[])
        assert connection.merge_port_map([(1, 0)], [0, 1], 2) == [[], [0]]

    def test_oversized_existing_map_is_truncated(self):
        connection = _connection(auto_ports=False, port_map=[[0], [1], [0], [1]])
        assert connection.merge_port_map([(0, 0)], [0], 2) == [[0], [1]]

    def test_multiple_targets_per_row_are_sorted(self):
        connection = _connection(auto_ports=False, port_map=[])
        assert connection.merge_port_map([(0, 1), (0, 0)], [0], 2) == [[0, 1], []]
