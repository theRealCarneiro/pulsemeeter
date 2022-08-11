import os
# import json

from pulsemeeter.settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainWindow():
    def __init__(self, client):
        self.builder = Gtk.Builder()
        getobj = self.builder.get_object
        self.builder.add_from_file(os.path.join(GLADEFILE, 'main_window.glade'))

        self.device_box_dict = {
            "vi": getobj('virtual_input_box'),
            "hi": getobj('hardware_input_box'),
            "a": getobj('hardware_output_box'),
            "b": getobj('virtual_output_box'),
            "sink-inputs": getobj('sink-input-box'),
            "source-inputs": getobj('source-input-box')
        }

        self.window = self.builder.get_object('window')

    def create_device(self, device_type, device):
        self.device_box_dict[device_type].pack_start(device, True, True, 0)

    def remove_device(self, device_type, device):
        box = self.device_box_dict[device_type]
        box.remove(device)

    def add_app(self, app, device_type):
        self.device_box_dict[device_type].pack_start(app, True, True, 0)

    def remove_app(self, app, device_type):
        self.device_box_dict[device_type].remove(app)

    # def create_virtual_input(self, name, mute, volume, primary):
        # device = VirtualInput(name, mute, volume, primary)
        # self.device_box_dict['vi'].pack_start(device, True, True, 0)

    # def create_hardware_input(self, name, mute, volume, rnnoise):
        # device = HardwareInput(name, mute, volume, rnnoise)
        # self.device_box_dict['hi'].pack_start(device, True, True, 0)

    # def add_a(self, name, mute, volume, eq):
        # device = HardwareOutput('VirtualInput', name, mute, volume, eq)
        # self.device_box_dict['vi'].pack_start(device, True, True, 0)

    # def add_b(self, name, mute, volume, primary, eq):
        # device = VirtualOutput('VirtualInput', name, mute, volume, primary, eq)
        # self.device_box_dict['vi'].pack_start(device, True, True, 0)

    # def add_app(self, index):
        # pass
