from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel


def _input_device(name='vi_a', channels=2, primary=False):
    return DeviceModel(
        name=name,
        channels=channels,
        channel_list=['front-left', 'front-right'][:channels],
        selected_channels=[True] * channels,
        device_type='source',
        device_class='virtual',
        primary=primary,
    )


def _output_device(name='b_a', channels=2, primary=False):
    return DeviceModel(
        name=name,
        channels=channels,
        channel_list=['front-left', 'front-right'][:channels],
        selected_channels=[True] * channels,
        device_type='sink',
        device_class='virtual',
        primary=primary,
    )


def _connection(nick='b_a', input_channels=2, output_channels=2, port_map=None):
    return ConnectionModel(
        nick=nick,
        input_sel_channels=[True] * input_channels,
        output_sel_channels=[True] * output_channels,
        port_map=port_map or [],
    )


def test_ensures_missing_top_level_buckets():
    config = ConfigModel(devices={'vi': {}})
    for key in ('vi', 'hi', 'a', 'b'):
        assert key in config.devices


def test_drops_devices_with_empty_name():
    bad = _input_device(name='')
    good = _input_device(name='keepme')
    config = ConfigModel(devices={'vi': {'1': bad, '2': good}, 'hi': {}, 'a': {}, 'b': {}})
    assert '1' not in config.devices['vi']
    assert '2' in config.devices['vi']


def test_dedupes_primary_within_type():
    a = _input_device(name='a', primary=True)
    b = _input_device(name='b', primary=True)
    config = ConfigModel(devices={'vi': {'1': a, '2': b}, 'hi': {}, 'a': {}, 'b': {}})
    primaries = [d.primary for d in config.devices['vi'].values()]
    assert primaries.count(True) == 1


def test_drops_orphan_connection_to_missing_output():
    inp = _input_device()
    inp.connections = {'a': {}, 'b': {'99': _connection(nick='ghost')}}
    config = ConfigModel(devices={'vi': {'1': inp}, 'hi': {}, 'a': {}, 'b': {}})
    assert config.devices['vi']['1'].connections['b'] == {}


def test_fills_missing_connection_for_existing_output():
    inp = _input_device()
    inp.connections = {'a': {}, 'b': {}}
    out = _output_device()
    config = ConfigModel(devices={'vi': {'1': inp}, 'hi': {}, 'a': {}, 'b': {'1': out}})
    assert '1' in config.devices['vi']['1'].connections['b']
    filled = config.devices['vi']['1'].connections['b']['1']
    assert isinstance(filled, ConnectionModel)


def test_resets_port_map_with_out_of_range_indices():
    inp = _input_device(channels=2)
    out = _output_device(channels=2)
    bad_conn = _connection(input_channels=2, output_channels=2, port_map=[[5], [0]])
    bad_conn.auto_ports = False
    inp.connections = {'a': {}, 'b': {'1': bad_conn}}
    config = ConfigModel(devices={'vi': {'1': inp}, 'hi': {}, 'a': {}, 'b': {'1': out}})
    repaired = config.devices['vi']['1'].connections['b']['1']
    assert repaired.port_map == []
    assert repaired.auto_ports is True


def test_resets_port_map_longer_than_input_channels():
    inp = _input_device(channels=2)
    out = _output_device(channels=2)
    bad_conn = _connection(input_channels=2, output_channels=2, port_map=[[0], [1], [0]])
    bad_conn.auto_ports = False
    inp.connections = {'a': {}, 'b': {'1': bad_conn}}
    config = ConfigModel(devices={'vi': {'1': inp}, 'hi': {}, 'a': {}, 'b': {'1': out}})
    assert config.devices['vi']['1'].connections['b']['1'].port_map == []


def test_ensures_connection_buckets_on_input_device():
    inp = _input_device()
    inp.connections = {}
    config = ConfigModel(devices={'vi': {'1': inp}, 'hi': {}, 'a': {}, 'b': {}})
    assert config.devices['vi']['1'].connections == {'a': {}, 'b': {}}
