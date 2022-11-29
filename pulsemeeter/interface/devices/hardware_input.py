import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import LAYOUT_DIR

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class HardwareInput(MinimalDevice):
    def __init__(self, client, device_type, device_id):
        builder = Gtk.Builder()
        getobj = builder.get_object
        name = client.config[device_type][device_id]['name']

        try:
            builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{client.config["layout"]}/hardware_input.glade'),
                ['hardware_input', 'adjust']
            )
        except Exception as ex:
            print(f'Error building hardware input {name}!\n{ex}')
            sys.exit(1)

        super().__init__(builder, client, device_type, device_id, nick=True)
        self.grid = builder.get_object('hardware_input')
        self.description = builder.get_object('description')
        self.rnnoise = builder.get_object('rnnoise')
        self.route_box = {"a": getobj('a_box'), "b": getobj('b_box')}
        self.route_dict = {"a": {}, "b": {}}
        self.create_route_buttons()

        self.description.set_label(self.device_config['description'])
        self.rnnoise.set_active(self.device_config['rnnoise'])
        self.rnnoise.connect('button_press_event', self.rnnoise_click)

        self.add(self.grid)
