import os
import sys
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class LatencyPopover():
    def __init__(self, button, sock, input_index, output_index):

        input_type = input_index[0]
        input_id = input_index[1]

        output_type = output_index[0]
        output_id = output_index[1]
        sink = output_type + output_id

        self.builder = Gtk.Builder()
        self.sock = sock
        layout = sock.config['layout']
        self.device_config = sock.config[input_type][input_id]

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{layout}.glade'),
                [
                    'latency_popover',
                    'latency_adjust',
                    'apply_latency_button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.latency_popover = self.builder.get_object('latency_popover')
        self.latency_popover.set_relative_to(button)

        self.latency_adjust = self.builder.get_object('latency_adjust')
        self.latency_adjust.set_value(self.device_config[sink + '_latency'])
        self.apply_latency_button = self.builder.get_object('apply_latency_button')
        self.apply_latency_button.connect('pressed', self.apply_latency, input_type, input_id, output_type, output_id)


        self.latency_popover.popup()

    def apply_latency(self, widget, input_type, input_id, output_type, output_id):
        sink = output_type + output_id
        latency = int(self.latency_adjust.get_value())
        self.sock.connect(input_type, input_id, output_type, output_id, True, latency)
