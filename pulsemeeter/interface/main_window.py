import os
# import json

from pulsemeeter.settings import GLADEFILE
from pulsemeeter.interface.popovers.device_creation import DeviceCreationPopOver

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainWindow():
    def __init__(self, client):
        self.builder = Gtk.Builder()
        getobj = self.builder.get_object
        self.builder.add_from_file(os.path.join(GLADEFILE, 'main_window.glade'))
        self.menu_popover = getobj('menu_popover')
        menu_button = getobj('menu_button')
        self.menu_popover.set_relative_to(menu_button)

        menu_button.connect('pressed', self.menu_popup)

        self.device_box_dict = {
            "vi": getobj('virtual_input_box'),
            "hi": getobj('hardware_input_box'),
            "a": getobj('hardware_output_box'),
            "b": getobj('virtual_output_box'),
            "sink-inputs": getobj('sink_input_box'),
            "source-outputs": getobj('source_output_box')
        }
        self.creation_popover = {}
        for device_type in ['hi', 'a', 'vi', 'b']:
            self.creation_popover[device_type] = DeviceCreationPopOver(client, device_type)
            add = getobj(f'add_{device_type}')
            add.connect('pressed', self.creation_popover[device_type].create_popup)

        self.window = self.builder.get_object('window')

    def menu_popup(self, widget):
        self.menu_popover.popup()

    def init_device(self, device_type, device):
        self.device_box_dict[device_type].pack_start(device, True, True, 0)

    def remove_device(self, device_type, device):
        box = self.device_box_dict[device_type]
        box.remove(device)

    def add_app(self, app, device_type):
        self.device_box_dict[device_type].pack_start(app, True, True, 0)

    def remove_app(self, app, device_type):
        self.device_box_dict[device_type].remove(app)
