import unittest
from pulsemeeter.model.device_model import DeviceModel


class TestDeviceModel(unittest.TestCase):
    '''
    Unit test for the device model
    '''

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.device = {
            'name': 'test_create',
            'channels': 2,
            'channel_list': [],
            'device_type': 'sink',
            'device_class': 'virtual'
        }

    def test_create_destroy(self):
        self.device['name'] = 'test_create'
        a = DeviceModel(**self.device)
        a.destroy()

    def test_mute(self):
        self.device['name'] = 'test_mute'
        a = DeviceModel(**self.device)
        a.set_mute(True)
        a.destroy()

    def test_primary(self):
        self.device['name'] = 'test_primary'
        a = DeviceModel(**self.device)
        a.set_default()
        a.destroy()

    def test_volume(self):
        self.device['name'] = 'test_volume'
        a = DeviceModel(**self.device)
        a.set_volume(15)
        a.destroy()


class TestClassMethods(unittest.TestCase):
    def test_list_devices(self):
        device_list = DeviceModel.list_devices('sink')
        assert isinstance(device_list, list)
        if len(device_list) > 0:
            device = device_list[0]
            assert isinstance(device, DeviceModel)
