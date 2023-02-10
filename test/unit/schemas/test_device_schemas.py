# from meexer.schemas.device_schema import 
# import unittest


# class TestDeviceIndex(unittest.TestCase):

    # def test_device_type_valid(self):
        # schemas.DeviceIndex(**{'device_type': 'vi', 'device_id': '1'})
        # schemas.DeviceIndex(**{'device_type': 'b', 'device_id': '1'})
        # schemas.DeviceIndex(**{'device_type': 'a', 'device_id': '1'})
        # schemas.DeviceIndex(**{'device_type': 'hi', 'device_id': '1'})

    # def test_device_type_invalid(self):
        # with self.assertRaises(ValueError):
            # schemas.DeviceIndex(**{'device_type': 's', 'device_id': '1'})
            # schemas.DeviceIndex(**{'device_type': 'hia', 'device_id': '1'})
            # schemas.DeviceIndex(**{'device_type': '1', 'device_id': '1'})
            # schemas.DeviceIndex(**{'device_type': '', 'device_id': '1'})

    # def test_device_id_valid(self):
        # schemas.DeviceIndex(**{'device_type': 'vi', 'device_id': '1'})
        # schemas.DeviceIndex(**{'device_type': 'a', 'device_id': '999'})

    # def test_device_id_invalid(self):
        # with self.assertRaises(ValueError):
            # schemas.DeviceIndex(**{'device_type': 's', 'device_id': '0'})
            # schemas.DeviceIndex(**{'device_type': 'hia', 'device_id': 'a'})
            # schemas.DeviceIndex(**{'device_type': '1', 'device_id': ''})
            # schemas.DeviceIndex(**{'device_type': '', 'device_id': ' '})


# class TestRemoveDevice(unittest.TestCase):

    # def test_index_valid(self):
        # schemas.RemoveDevice(**{'index': {'device_type': 'vi', 'device_id': '1'}})
        # schemas.RemoveDevice(**{'index': {'device_type': 'hi', 'device_id': '1'}})
        # schemas.RemoveDevice(**{'index': {'device_type': 'a', 'device_id': '1'}})
        # schemas.RemoveDevice(**{'index': {'device_type': 'b', 'device_id': '1'}})

    # def test_index_invalid(self):
        # with self.assertRaises(ValueError):
            # schemas.RemoveDevice(**{'index': {'device_type': 'v', 'device_id': '1'}})
            # schemas.RemoveDevice(**{'index': {'device_type': 'vi', 'device_id': '0'}})
