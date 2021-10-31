import os
from .settings import GLADEFILE
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class LatencyPopover():
    def __init__(self, button, pulse, index):

        self.config = pulse.config
        self.builder = Gtk.Builder()

        try:
            self.builder.add_objects_from_file(
                GLADEFILE,
                [
                    'latency_popover',
                    'latency_adjust',
                    'apply_latency_button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.Latency_Popover = self.builder.get_object('latency_popover')
        self.Latency_Popover.set_relative_to(button)

        self.Latency_Adjust = self.builder.get_object('latency_adjust')
        self.Latency_Adjust.set_value(self.config[index[0]][index[1]][index[2] + '_latency'])
        self.Apply_Latency_Button = self.builder.get_object('apply_latency_button')
        self.Apply_Latency_Button.connect('pressed', self.apply_latency, index, pulse)


        self.Latency_Popover.popup()

    def apply_latency(self, widget, index, pulse):
        val = int(self.Latency_Adjust.get_value())
        self.config[index[0]][index[1]][index[2] + '_latency'] = val
        if self.config[index[0]][index[1]][index[2]] == False:
            return
        dev = list(index[2])
        command = ''
        command = command + pulse.connect('disconnect', [index[0], index[1]], dev, 'init')
        command = command + pulse.connect('connect', [index[0], index[1]], dev, 'init')
        # print(command)
        os.popen(command)

