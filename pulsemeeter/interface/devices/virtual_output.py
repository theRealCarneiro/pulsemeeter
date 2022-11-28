import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import LAYOUT_DIR

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class VirtualOutput(MinimalDevice):
    def __init__(self, client, device_type, device_id):
        builder = Gtk.Builder()
        name = client.config[device_type][device_id]['name']

        try:
            builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{client.config["layout"]}/virtual_output.glade'),
                ['virtual_output', 'adjust', 'label_event_box']
            )
        except Exception as ex:
            print(f'Error building virtual output {name}!\n{ex}')
            sys.exit(1)

        super(VirtualOutput, self).__init__(builder, client, device_type, device_id)
        self.grid = builder.get_object('virtual_output')
        self.primary = builder.get_object('primary')
        self.eq = builder.get_object('eq')

        self.eq.set_active(self.device_config['eq'])
        self.eq.connect('button_press_event', self.eq_click)
        self.primary.set_active(self.device_config['primary'])
        self.primary.set_sensitive(not self.device_config['primary'])

        self.add(self.grid)
