import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class HardwareOutput(MinimalDevice):
    def __init__(self, name, mute, volume, eq):
        builder = Gtk.Builder()

        try:
            builder.add_objects_from_file(
                os.path.join(GLADEFILE, 'hardware_output.glade'),
                ['hardware_output', 'adjust']
            )
        except Exception as ex:
            print(f'Error building hardware output {name}!\n{ex}')
            sys.exit(1)

        super(HardwareOutput, self).__init__(builder, name, mute, volume)
        self.grid = builder.get_object('hardware_output')
        self.eq = builder.get_object('eq')

        self.eq.set_active(eq)

        self.add(self.grid)
