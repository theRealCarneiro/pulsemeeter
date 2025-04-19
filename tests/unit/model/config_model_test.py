import unittest
from pulsemeeter.model.config_model import ConfigModel


class TestConfig(unittest.TestCase):

    def test_create(self):
        ConfigModel()
        # raise TypeError

    def test_save(self):
        ConfigModel().write()
