import subprocess
import unittest


class InitRemove(unittest.TestCase):

    def test_1_should_init(self):
        command = 'pmctl init sink test_init_sink_1 1'
        subprocess.check_call(command.split())

        command = 'pmctl init sink test_init_source_1 2'
        subprocess.check_call(command.split())

        command = 'pmctl remove test_init_sink_1 '
        subprocess.check_call(command.split())

        command = 'pmctl remove test_init_source_1'
        subprocess.check_call(command.split())

    def test_2_exists(self):

        with self.assertRaises(subprocess.CalledProcessError):

            command = 'pmctl init sink test_sink_1 1'
            subprocess.check_call(command.split())
            command = 'pmctl init source test_source_1 1'
            subprocess.check_call(command.split())

    def invalid_channels(self):
        with self.assertRaises(subprocess.CalledProcessError):
            command = 'pmctl init sink test a'
            subprocess.check_call(command.split())

    def invalid_name(self):
        with self.assertRaises(subprocess.CalledProcessError):
            command = 'pmctl init sink 2test 1'
            subprocess.check_call(command.split())

    def no_channels(self):
        with self.assertRaises(subprocess.CalledProcessError):
            # no channels
            command = 'pmctl remove idontexist'
            subprocess.check_call(command.split())


class Remove(unittest.TestCase):

    def should_remove(self):
        command = 'pmctl init sink test_remove_sink_1 1'
        subprocess.check_call(command.split())

        command = 'pmctl init sink test_remove_source_1 2'
        subprocess.check_call(command.split())

        command = 'pmctl remove test_remove_sink_1'
        subprocess.check_call(command.split())

        command = 'pmctl remove test_remove_source_1'
        subprocess.check_call(command.split())

    def invalid_name(self):

        with self.assertRaises(subprocess.CalledProcessError):

            command = 'pmctl remove 2test'
            subprocess.check_call(command.split())

    def doesnt_exist(self):
        with self.assertRaises(subprocess.CalledProcessError):
            command = 'pmctl remove idontexist'
            subprocess.check_call(command.split())
