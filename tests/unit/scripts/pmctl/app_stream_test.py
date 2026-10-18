import asyncio
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest import mock

import pulsectl
from pulsectl import PulseSinkInputInfo, PulseSourceOutputInfo

from pulsemeeter.scripts import pmctl, pmctl_async


# pipewire-pulse gives a sink and its monitor source the same index, so a
# lookup in the wrong namespace finds a real, but wrong, device
DEVICE_INDEX = 3
SINK = SimpleNamespace(name='test_sink')
SOURCE = SimpleNamespace(name='test_sink.monitor')


def _stream(app_type, index=7, object_id='42', node_name='test_app_node'):
    '''A real pulsectl stream object: a sink input has .sink, a source output has .source.'''
    cls = PulseSinkInputInfo if app_type == 'sink_input' else PulseSourceOutputInfo
    fields = dict.fromkeys(cls.c_struct_fields.split(), 0)
    fields.update({'index': index, 'sink' if app_type == 'sink_input' else 'source': DEVICE_INDEX})
    stream = cls(**fields)
    stream.proplist = {'application.name': 'test_app', 'node.name': node_name}
    if object_id is not None:
        stream.proplist['object.id'] = object_id
    stream.volume = pulsectl.PulseVolumeInfo(1.0, 2)
    return stream


def _lookup(objects):
    def lookup(index):
        if index not in objects:
            raise pulsectl.PulseIndexError(index)
        return objects[index]
    return lookup


def _fake_pulse(streams, info=mock.Mock):
    '''A pulse connection serving these streams, plus SINK and SOURCE at DEVICE_INDEX.'''
    pulse = mock.Mock()
    sink_inputs = {s.index: s for s in streams if isinstance(s, PulseSinkInputInfo)}
    source_outputs = {s.index: s for s in streams if isinstance(s, PulseSourceOutputInfo)}
    pulse.sink_input_list.return_value = list(sink_inputs.values())
    pulse.source_output_list.return_value = list(source_outputs.values())
    pulse.sink_input_info = info(side_effect=_lookup(sink_inputs))
    pulse.source_output_info = info(side_effect=_lookup(source_outputs))
    pulse.sink_info = info(side_effect=_lookup({DEVICE_INDEX: SINK}))
    pulse.source_info = info(side_effect=_lookup({DEVICE_INDEX: SOURCE}))
    return pulse


class _AppStreamCases:
    '''Shared cases; subclasses set the stream type and the device it should resolve to.'''
    APP_TYPE = None
    DEVICE = None

    def setUp(self):
        self.app = _stream(self.APP_TYPE)
        self.pulse = _fake_pulse([self.app])
        patcher = mock.patch.object(pmctl, 'PULSE', self.pulse)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_app_by_id_resolves_own_device(self):
        app = pmctl.app_by_id(self.app.index, self.APP_TYPE)
        assert app is self.app
        assert app.device_name == self.DEVICE.name

    def test_app_mute(self):
        assert pmctl.app_mute(self.APP_TYPE, self.app.index, True)
        self.pulse.mute.assert_called_once_with(self.app, True)

    def test_app_volume_keeps_channel_count(self):
        assert pmctl.app_volume(self.APP_TYPE, self.app.index, 50)
        app, volume = self.pulse.volume_set.call_args.args
        assert app is self.app
        assert volume.values == [0.5, 0.5]

    def test_get_app_object_id(self):
        assert pmctl.get_app_object_id(self.app.index, self.APP_TYPE) == 42

    def test_get_app_object_id_does_not_need_device(self):
        self.pulse.sink_info.side_effect = pulsectl.PulseIndexError(DEVICE_INDEX)
        self.pulse.source_info.side_effect = pulsectl.PulseIndexError(DEVICE_INDEX)
        assert pmctl.get_app_object_id(self.app.index, self.APP_TYPE) == 42

    def test_get_app_object_id_missing_stream(self):
        assert pmctl.get_app_object_id(self.app.index + 1, self.APP_TYPE) is None

    def test_get_app_object_id_without_object_id(self):
        del self.app.proplist['object.id']
        assert pmctl.get_app_object_id(self.app.index, self.APP_TYPE) is None

    def test_list_apps_resolves_own_device_and_skips_loopbacks(self):
        loopback = _stream(self.APP_TYPE, index=8, node_name='input.pm_route_test_sink_to_test_out')
        self.pulse = _fake_pulse([self.app, loopback])
        with mock.patch.object(pmctl, 'PULSE', self.pulse):
            apps = pmctl.list_apps(self.APP_TYPE)
        assert apps == [self.app]
        assert apps[0].device_name == self.DEVICE.name

    def test_async_get_app_by_id_resolves_own_device(self):
        pulse = _fake_pulse([self.app], info=mock.AsyncMock)

        @asynccontextmanager
        async def connection(client_name=None):
            yield pulse

        with mock.patch.object(pmctl_async, 'pulse_connection', connection):
            app = asyncio.run(pmctl_async.get_app_by_id(self.APP_TYPE, self.app.index))
        assert app is self.app
        assert app.device_name == self.DEVICE.name


class TestSinkInput(_AppStreamCases, unittest.TestCase):
    APP_TYPE = 'sink_input'
    DEVICE = SINK


class TestSourceOutput(_AppStreamCases, unittest.TestCase):
    APP_TYPE = 'source_output'
    DEVICE = SOURCE


class TestSubscribePeak(unittest.TestCase):
    '''App vumeters: pulse can only monitor a sink input on its own.'''

    def _subscribe(self, device_type, stream_index, peaks, gain=None):
        pulse = mock.Mock()

        async def subscribe_peak_sample(name, rate, stream_idx=None):
            for peak in peaks:
                yield peak
        pulse.subscribe_peak_sample = mock.Mock(side_effect=subscribe_peak_sample)

        @asynccontextmanager
        async def connection(client_name=None):
            yield pulse

        received = []

        async def callback(peak):
            received.append(peak)

        with mock.patch.object(pmctl_async, 'pulse_connection', connection):
            asyncio.run(pmctl_async.subscribe_peak(
                'test_device', device_type, callback, stream_index=stream_index, gain=gain
            ))
        return pulse, received

    def test_sink_input_meters_its_own_stream(self):
        pulse, received = self._subscribe('sink', 7, [0.5])
        pulse.subscribe_peak_sample.assert_called_once_with('test_device.monitor', 30, stream_idx=7)
        assert received == [0.5]

    def test_source_output_meters_source_scaled_by_gain(self):
        pulse, received = self._subscribe('source', 7, [0.5], gain=lambda: 0.125)
        pulse.subscribe_peak_sample.assert_called_once_with('test_device', 30, stream_idx=None)
        assert received == [0.0625]

    def test_gain_is_read_for_every_peak(self):
        # the slider changes the gain while the meter keeps running
        gains = iter([1.0, 0.125, 0.0])
        _, received = self._subscribe('source', 7, [0.5, 0.5, 0.5], gain=lambda: next(gains))
        assert received == [0.5, 0.0625, 0.0]


if __name__ == '__main__':
    unittest.main()
