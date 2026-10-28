from pulsemeeter.model.connection_model import ConnectionModel, pair_match

STEREO_CAPTURE = ['capture_FL', 'capture_FR']
STEREO_PLAYBACK = ['playback_FL', 'playback_FR']
MONO_PLAYBACK = ['playback_MONO']

STEREO = [(0, 'FL'), (1, 'FR')]
MONO = [(0, 'MONO')]

# A surround device whose channel order starts with FC, as some do, so index 0 is not FL
SURROUND_71 = [
    (0, 'FC'), (1, 'FL'), (2, 'FR'), (3, 'LFE'),
    (4, 'RL'), (5, 'RR'), (6, 'SL'), (7, 'SR'),
]
SURROUND_71_PORTS = [
    'playback_FC', 'playback_FL', 'playback_FR', 'playback_LFE',
    'playback_RL', 'playback_RR', 'playback_SL', 'playback_SR',
]


def _connection(auto_ports=True, port_map=None):
    return ConnectionModel(
        nick='out',
        auto_ports=auto_ports,
        input_sel_channels=[True, True],
        output_sel_channels=[True, True],
        port_map=port_map or [],
    )


class TestPairMatch:

    def test_surround_to_stereo_only_pairs_shared_positions(self):
        # Only FL and FR have a home; the other six must not be summed into both speakers
        assert pair_match(SURROUND_71, STEREO) == [(1, 0), (2, 1)]

    def test_channel_order_is_irrelevant(self):
        # A device that reports FL before FC must still route centre to centre
        reordered = [(0, 'FL'), (1, 'FR'), (2, 'FC')]
        assert pair_match([(0, 'FC'), (1, 'FL'), (2, 'FR')], reordered) == [(0, 2), (1, 0), (2, 1)]

    def test_stereo_to_mono_folds_both_channels(self):
        assert pair_match(STEREO, MONO) == [(0, 0), (1, 0)]

    def test_repeated_names_pair_one_to_one(self):
        # UNK repeats for every unplaced channel and must not collapse onto the first one
        unknown = [(0, 'UNK'), (1, 'UNK'), (2, 'UNK')]
        assert pair_match(unknown, unknown) == [(0, 0), (1, 1), (2, 2)]

    def test_stereo_to_four_aux_outputs_takes_the_first_two(self):
        aux = [(0, 'AUX0'), (1, 'AUX1'), (2, 'AUX2'), (3, 'AUX3')]
        assert pair_match(STEREO, aux) == [(0, 0), (1, 1)]

    def test_lone_named_input_is_duplicated(self):
        # One mic channel picked off an analog interface must not play in one ear only
        assert pair_match([(0, 'FL')], STEREO) == [(0, 0), (0, 1)]

    def test_partial_match_does_not_fall_back_to_index(self):
        # capture_1 replaced monitor_FL, and FR must not shift onto the left speaker
        assert pair_match([(0, 'FR'), (1, '1')], STEREO) == [(0, 1)]


class TestStrPortMap:

    def test_manual_map_uses_absolute_channel_indexes(self):
        connection = _connection(auto_ports=False, port_map=[[0], [1]])
        assert connection.str_port_map([(1, 'FL'), (2, 'FR')], STEREO) == '1:0 2:1'

    def test_manual_map_longer_than_the_channel_list(self):
        # The map outlives the device: the surplus rows must not raise
        connection = _connection(auto_ports=False, port_map=[[0], [0], [0]])
        assert connection.str_port_map(MONO, MONO) == '0:0'


class TestRoutingGridAutoPorts:

    def test_stereo_to_stereo(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, STEREO_PLAYBACK, STEREO, STEREO
        )
        assert rows == [(0, 'capture_FL'), (1, 'capture_FR')]
        assert cols == [(0, 'playback_FL'), (1, 'playback_FR')]
        assert checked == {(0, 0), (1, 1)}

    def test_stereo_to_mono_folds_into_the_single_column(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, STEREO, MONO
        )
        assert len(rows) == 2
        assert len(cols) == 1
        assert checked == {(0, 0), (1, 0)}

    def test_input_config_claims_more_channels_than_it_has_ports(self):
        rows, cols, checked = _connection().routing_grid(
            ['capture_MONO'], STEREO_PLAYBACK, STEREO, STEREO
        )
        assert rows == [(0, 'capture_MONO')]
        assert len(cols) == 2
        assert checked == {(0, 0)}

    def test_surround_to_stereo_checks_only_the_shared_channels(self):
        rows, cols, checked = _connection().routing_grid(
            SURROUND_71_PORTS, STEREO_PLAYBACK, SURROUND_71, STEREO
        )
        assert len(rows) == 8
        assert len(cols) == 2
        # FL is row 1 and FR is row 2 of this channel order
        assert checked == {(1, 0), (2, 1)}

    def test_deselected_input_channel_keeps_its_own_port_name(self):
        # Only channel 1 selected: its row shows channel 1's port, and a lone channel plays on both sides
        rows, _cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, STEREO_PLAYBACK, [(1, 'FR')], STEREO
        )
        assert rows == [(0, 'capture_FR')]
        assert checked == {(0, 0), (0, 1)}

    def test_output_device_gone(self):
        rows, cols, checked = _connection().routing_grid(
            STEREO_CAPTURE, [], STEREO, STEREO
        )
        assert len(rows) == 2
        assert cols == []
        assert checked == set()


class TestRoutingGridManualPorts:

    def test_target_without_a_port_is_dropped(self):
        rows, cols, checked = _connection(auto_ports=False, port_map=[[1]]).routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, STEREO, STEREO
        )
        assert len(rows) == 2
        assert len(cols) == 1
        assert checked == set()

    def test_downmix_map_is_kept(self):
        _rows, _cols, checked = _connection(auto_ports=False, port_map=[[0], [0]]).routing_grid(
            STEREO_CAPTURE, MONO_PLAYBACK, STEREO, STEREO
        )
        assert checked == {(0, 0), (1, 0)}

    def test_position_without_a_live_input_port_is_ignored(self):
        _rows, _cols, checked = _connection(auto_ports=False, port_map=[[0], [1]]).routing_grid(
            ['capture_MONO'], STEREO_PLAYBACK, STEREO, STEREO
        )
        assert checked == {(0, 0)}

    def test_map_longer_than_the_channel_list(self):
        _rows, _cols, checked = _connection(
            auto_ports=False, port_map=[[0], [1], [0], [1]]
        ).routing_grid(STEREO_CAPTURE, STEREO_PLAYBACK, STEREO, STEREO)
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


class TestWarningText:

    def test_every_kind_of_gap_gets_a_line(self):
        connection = _connection()
        connection.unrouted_ports = ['monitor_FC', 'monitor_LFE']
        connection.missing_links = 2
        connection.failed_pairs = ['monitor_FR -> playback_FR']
        assert connection.warning_text() == (
            'FC, LFE not routed\n'
            'Links to missing channels in the manual map: 2\n'
            'Failed to link: monitor_FR -> playback_FR'
        )
