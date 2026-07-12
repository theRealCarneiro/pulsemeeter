import unittest

from pulsemeeter.model.device_model import DeviceModel


def _device(**overrides):
    '''Build a valid virtual sink DeviceModel, overriding fields as needed.'''
    kwargs = {
        'name': 'test_device',
        'channels': 2,
        'channel_list': ['front-left', 'front-right'],
        'selected_channels': [True, True],
        'device_type': 'sink',
        'device_class': 'virtual',
        'primary': False,
    }
    kwargs.update(overrides)
    return DeviceModel(**kwargs)


class _FakeVolume:
    def __init__(self, values):
        self.values = values


class _FakePaDevice:
    '''Minimal stand-in for a pulsectl PulseSinkInfo/PulseSourceInfo.'''
    def __init__(self, name, description, channel_list, values, mute=False, proplist=None):
        self.name = name
        self.description = description
        self.channel_list = channel_list
        self.volume = _FakeVolume(values)
        self.mute = mute
        self.proplist = proplist or {}


class TestDeviceModel(unittest.TestCase):
    '''Unit tests for the device data model.'''

    def test_create(self):
        device = _device(name='test_create')
        self.assertEqual(device.name, 'test_create')
        self.assertEqual(device.channels, 2)
        self.assertFalse(device.mute)

    def test_nick_and_description_default_to_name(self):
        device = _device(name='test_nick')
        self.assertEqual(device.nick, 'test_nick')
        self.assertEqual(device.description, 'test_nick')

    def test_volume_defaults_to_full_per_channel(self):
        device = _device()
        self.assertEqual(device.volume, [100, 100])

    def test_hardware_device_has_no_primary(self):
        device = _device(device_class='hardware')
        self.assertIsNone(device.primary)

    def test_invalid_name_raises(self):
        with self.assertRaises(ValueError):
            _device(name=' leading_space')
        with self.assertRaises(ValueError):
            _device(name='trailing_space ')

    def test_set_mute(self):
        device = _device(name='test_mute')
        device.set_mute(True)
        self.assertTrue(device.mute)
        device.set_mute(False)
        self.assertFalse(device.mute)

    def test_set_volume(self):
        device = _device(name='test_volume')
        device.set_volume(15)
        self.assertEqual(device.volume, [15, 15])

    def test_set_primary(self):
        device = _device(name='test_primary')
        device.set_primary(True)
        self.assertTrue(device.primary)


class TestClassMethods(unittest.TestCase):

    def test_pa_to_device_model_virtual(self):
        pa_device = _FakePaDevice(
            name='virtual_sink',
            description='Virtual Sink',
            channel_list=['front-left', 'front-right'],
            values=[1.0, 0.5],
            proplist={'factory.name': 'support.null-audio-sink'},
        )
        device = DeviceModel.pa_to_device_model(pa_device, 'sink')
        self.assertIsInstance(device, DeviceModel)
        self.assertEqual(device.device_class, 'virtual')
        self.assertEqual(device.channels, 2)
        self.assertEqual(device.volume, [100, 50])

    def test_pa_to_device_model_hardware(self):
        pa_device = _FakePaDevice(
            name='alsa_output.hw',
            description='Speakers',
            channel_list=['front-left', 'front-right'],
            values=[1.0, 1.0],
            proplist={},
        )
        device = DeviceModel.pa_to_device_model(pa_device, 'sink')
        self.assertEqual(device.device_class, 'hardware')

    def test_list_devices(self):
        pa_device_list = [
            _FakePaDevice(
                name='alsa_output.hw',
                description='Speakers',
                channel_list=['front-left', 'front-right'],
                values=[1.0, 1.0],
                proplist={},
            ),
        ]
        device_list = DeviceModel.list_devices(pa_device_list, 'sink')
        self.assertIsInstance(device_list, list)
        self.assertEqual(len(device_list), 1)
        self.assertIsInstance(device_list[0], DeviceModel)

    def test_list_devices_empty(self):
        self.assertEqual(DeviceModel.list_devices([], 'sink'), [])
