import unittest
from meexer.api import device_api
from pydantic import error_wrappers
# from meexer.schemas import requests_schema


class TestCreateDevice(unittest.TestCase):
    '''
    This is for testing creation and destruction of devices
    '''

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.device = {
            'name': '',
            'channels': 2,
            'channel_list': [],
            'device_type': 'sink',
            'device_class': 'virtual'
        }

    def test_create_device(self):

        self.device['name'] = 'test_create_device'
        req = {'device': self.device}
        device = device_api.create_device(req)
        device.destroy()

    def test_create_invalid_device(self):

        self.device['name'] = 'test_create_invalid_device'
        del self.device['channels']
        req = {'device': self.device}
        with self.assertRaises(error_wrappers.ValidationError):
            device_api.create_device(req)

        self.device['channels'] = 2

    def test_create_empty_device(self):
        req = {'device': {}}
        with self.assertRaises(error_wrappers.ValidationError):
            device_api.create_device(req)


class TestMuteDevice(unittest.TestCase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.device = {
            'name': '',
            'channels': 2,
            'channel_list': [],
            'device_type': 'sink',
            'device_class': 'virtual'
        }

    def test_mute_invalid_state(self):

        # setup device
        self.device['name'] = 'test_mute_invalid_state'
        req = {'device': self.device}
        device = device_api.create_device(req)

        # get device id
        did = list(device_api.CONFIG.vi.keys())[list(device_api.CONFIG.vi.values()).index(device)]

        # mute request
        mute_req = {'index': {'device_type': 'vi', 'device_id': did}, 'state': 'lambda'}
        with self.assertRaises(error_wrappers.ValidationError):
            device_api.mute(mute_req)
            mute_req['state'] = 'house'
            device_api.mute(mute_req)
        device.destroy()

    def test_mute_device(self):

        # setup device
        self.device['name'] = 'test_mute_pass'
        req = {'device': self.device}
        device = device_api.create_device(req)

        # get device id
        did = list(device_api.CONFIG.vi.keys())[list(device_api.CONFIG.vi.values()).index(device)]

        # mute request
        mute_req = {'index': {'device_type': 'vi', 'device_id': did}, 'state': True}
        device_api.mute(mute_req)
        mute_req['state'] = False
        device_api.mute(mute_req)
        device.destroy()


class TestDefaultDevice(unittest.TestCase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.device = {
            'name': '',
            'channels': 2,
            'channel_list': [],
            'device_type': 'sink',
            'device_class': 'virtual'
        }

    def test_default(self):

        # setup device
        self.device['name'] = 'test_default'
        req = {'device': self.device}
        device = device_api.create_device(req)

        # get device id
        did = list(device_api.CONFIG.vi.keys())[list(device_api.CONFIG.vi.values()).index(device)]

        # default request
        default_req = {'index': {'device_type': 'vi', 'device_id': did}}
        device_api.default(default_req)
        device.destroy()
