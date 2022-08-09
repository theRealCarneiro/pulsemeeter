import os
import sys

from pulsemeeter.interface.devices.minimal_device import MinimalDevice
from pulsemeeter.settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class VirtualOutput(MinimalDevice):
    def __init__(self, name, mute, volume, primary, eq):
        builder = Gtk.Builder()

        try:
            builder.add_objects_from_file(
                os.path.join(GLADEFILE, 'virtual_output.glade'),
                ['virtual_output', 'adjust', 'label_event_box']
            )
        except Exception as ex:
            print(f'Error building virtual output {name}!\n{ex}')
            sys.exit(1)

        super(VirtualOutput, self).__init__(builder, name, mute, volume)
        self.grid = builder.get_object('virtual_output')
        self.primary = builder.get_object('primary')
        self.eq = builder.get_object('eq')

        self.eq.set_active(eq)
        self.primary.set_active(primary)
        self.primary.set_sensitive(not primary)

        self.add(self.grid)
