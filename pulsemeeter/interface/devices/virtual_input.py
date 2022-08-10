import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class VirtualInput(MinimalDevice):
    def __init__(self, name, mute, volume, primary):
        builder = Gtk.Builder()
        getobj = builder.get_object

        try:
            builder.add_objects_from_file(
                os.path.join(GLADEFILE, 'virtual_input.glade'),
                ['virtual_input', 'adjust']
            )
        except Exception as ex:
            print(f'Error building virtual input {name}!\n{ex}')
            sys.exit(1)

        super(VirtualInput, self).__init__(builder, name, mute, volume)
        self.grid = builder.get_object('virtual_input')
        self.primary = builder.get_object('primary')
        self.route_box = {"a": getobj('a_box'), "b": getobj('b_box')}
        self.route_dict = {"a": {}, "b": {}}

        self.primary.set_active(primary)
        self.primary.set_sensitive(not primary)

        self.add(self.grid)