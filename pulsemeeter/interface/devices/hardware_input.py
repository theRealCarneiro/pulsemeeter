import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class HardwareInput(MinimalDevice):
    def __init__(self, name, mute, volume, rnnoise):
        builder = Gtk.Builder()
        getobj = builder.get_object

        try:
            builder.add_objects_from_file(
                os.path.join(GLADEFILE, 'hardware_input.glade'),
                ['hardware_input', 'adjust']
            )
        except Exception as ex:
            print(f'Error building hardware input {name}!\n{ex}')
            sys.exit(1)

        super(HardwareInput, self).__init__(builder, name, mute, volume)
        self.grid = builder.get_object('hardware_input')
        self.rnnoise = builder.get_object('rnnoise')
        self.route_box = {"a": getobj('a_box'), "b": getobj('b_box')}
        self.route_dict = {"a": {}, "b": {}}

        self.rnnoise.set_active(rnnoise)

        self.add(self.grid)
