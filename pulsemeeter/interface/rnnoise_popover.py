import os
import sys
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class RnnoisePopover():
    def __init__(self, button, sock, deivce_type, device_id):

        self.builder = Gtk.Builder()
        self.sock = sock
        self.device_config = sock.config['hi'][device_id]
        layout = sock.config['layout']

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{layout}.glade'),
                [
                    'rnnoise_popover',
                    'rnnoise_latency_adjust',
                    'rnnoise_threshold_adjust',
                    'apply_rnnoise_button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.rnnoise_popover = self.builder.get_object('rnnoise_popover')
        self.rnnoise_popover.set_relative_to(button)

        self.rnnoise_latency_adjust = self.builder.get_object('rnnoise_latency_adjust')
        self.rnnoise_latency_adjust.set_value(self.device_config['rnnoise_latency'])

        self.rnnoise_threshold_adjust = self.builder.get_object('rnnoise_threshold_adjust')
        self.rnnoise_threshold_adjust.set_value(self.device_config['rnnoise_control'])

        self.apply_rnnoise_button = self.builder.get_object('apply_rnnoise_button')
        self.apply_rnnoise_button.connect('pressed', self.apply_button, device_id)

        self.rnnoise_popover.popup()

    def apply_button(self, widget, device_id):
        latency = int(self.rnnoise_latency_adjust.get_value())
        # self.device_config['rnnoise_latency'] = val

        control = int(self.rnnoise_threshold_adjust.get_value())
        # self.device_config['rnnoise_control'] = val

        if self.device_config['use_rnnoise'] == False:
            return

        self.sock.rnnoise(device_id, 'set', control, latency)
        # sink_name = self.device_config['rnnoise_name']
        # print(command)

