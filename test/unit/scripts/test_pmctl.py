import unittest
from meexer.scripts import pmctl


class TestCreation(unittest.TestCase):

    def test_invalid_device_type(self):
        pass

    def test_init_invalid_device_name_regex(self):
        '''
        Should fail, return an error
        '''
        pass

    def test_empty_device_name(self):
        '''
        Should fail, return an error
        '''
        ret = pmctl.init('sink', '')
        assert ret == 1

    def test_device_exists(self):
        '''
        Should fail, return an error
        '''
        pmctl.init('sink', 'device_exists')
        ret = pmctl.init('sink', 'device_exists')
        assert ret == 1

        ret = pmctl.remove('device_exists')
        assert ret == 0

    def test_device_not_exists(self):
        '''
        Should fail, return an error
        '''
        ret = pmctl.init('sink', 'device_not_exists')
        assert ret == 0
        ret = pmctl.remove('device_not_exists')
        assert ret == 0

    def test_remove_not_exist(self):
        '''
        '''
        ret = pmctl.remove('remove_not_exists')
        assert ret == 1


# class TestConnect(unittest.TestCase):

    # def __init__(self):
        # pass


class TestMute(unittest.TestCase):

    def test_mute_true(self):
        pmctl.init('sink', 'test_mute_true')
        res = pmctl.mute('sink', 'test_mute_true', True)
        pmctl.remove('test_mute_true')
        assert res == 0

    def test_mute_false(self):
        pmctl.init('sink', 'test_mute_false')
        res = pmctl.mute('sink', 'test_mute_false', False)
        pmctl.remove('test_mute_false')
        assert res == 0


class TestPrimary(unittest.TestCase):

    def test_primary(self):
        pmctl.init('sink', 'test_primary')
        res = pmctl.set_primary('sink', 'test_primary')
        assert res == 0
        pmctl.remove('test_primary')


class TestVolume(unittest.TestCase):

    def test_volume_valid(self):
        pmctl.init('sink', 'test_volume_valid')
        res = pmctl.volume('sink', 'test_volume_valid', 15)
        assert res == 0
        pmctl.remove('test_volume_valid')
