import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import LAYOUT_DIR

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class HardwareOutput(MinimalDevice):
    def __init__(self, client, device_type, device_id):
        builder = Gtk.Builder()
        name = client.config[device_type][device_id]['name']

        try:
            builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{client.config["layout"]}/hardware_output.glade'),
                ['hardware_output', 'adjust']
            )
        except Exception as ex:
            print(f'Error building hardware output {name}!\n{ex}')
            sys.exit(1)

        super(HardwareOutput, self).__init__(builder, client, device_type, device_id,
                                             nick=True)

        self.grid = builder.get_object('hardware_output')
        self.description = builder.get_object('description')
        self.eq = builder.get_object('eq')

        self.description.set_label(self.device_config['description'])
        self.eq.set_active(self.device_config['eq'])
        self.eq.connect('button_press_event', self.eq_click)

        self.add(self.grid)
