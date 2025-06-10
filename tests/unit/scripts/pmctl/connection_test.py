import subprocess
import unittest


class Connect(unittest.TestCase):

    def __init__(self):
        command = 'pmctl init sink test_mono 1\n'
        command += 'pmctl init source tests_mono 1\n'
        command += 'pmctl init sink test_stereo 2\n'
        command += 'pmctl init source tests_stereo 2\n'
        command += 'pmctl init sink test_quad 4\n'
        command += 'pmctl init source tests_quad 4\n'
        subprocess.check_call(command.split())

    # with auto ports doesnt mather the number of channels
    def auto_ports_exists(self):
        command = 'pmctl connect test_mono tests_mono'
        subprocess.check_call(command.split())

        command = 'pmctl disconnect test_mono tests_mono'
        subprocess.check_call(command.split())

    def auto_ports_doest_exist(self):
        with self.assertRaises(subprocess.CalledProcessError):
            command = 'pmctl connect test tests_mono'
            subprocess.check_call(command.split())

            command = 'pmctl disconnect test tests_mono'
            subprocess.check_call(command.split())

    def manual_ports(self):
        command = ['pmctl', 'connect', 'testc', 'testsc', '0:1 1:3']
        subprocess.check_call(command)
        command = 'pmctl disconnect testc testsc'
        subprocess.check_call(command.split())
        command = ['pmctl', 'connect', 'testsc', 'testc', '3:1 0:0']
        subprocess.check_call(command)
        command = ['pmctl', 'disconnect', 'testc', 'testsc', '3:1']
        subprocess.check_call(command)

        # should fail
        with self.assertRaises(subprocess.CalledProcessError):
            command = 'pmctl connect dontexist dontexist2'
            subprocess.check_call(command.split())
            command = 'pmctl disconnect dontexist dontexist2'
            subprocess.check_call(command.split())
            command = 'pmctl connect 1dontexist dontexist2'
            subprocess.check_call(command.split())
            command = 'pmctl disconnect 1dontexist dontexist2'
            subprocess.check_call(command.split())

