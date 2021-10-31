import os
from .settings import GLADEFILE
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class RnnoisePopover():
    def __init__(self, button, pulse, index):

        self.pulse = pulse
        self.builder = Gtk.Builder()

        try:
            self.builder.add_objects_from_file(
                GLADEFILE,
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

        self.Rnnoise_Popover = self.builder.get_object('rnnoise_popover')
        self.Rnnoise_Popover.set_relative_to(button)

        self.Rnnoise_Latency_Adjust = self.builder.get_object('rnnoise_latency_adjust')
        self.Rnnoise_Latency_Adjust.set_value(self.pulse.config[index[0]][index[1]]['rnnoise_latency'])

        self.Rnnoise_Threshold_Adjust = self.builder.get_object('rnnoise_threshold_adjust')
        self.Rnnoise_Threshold_Adjust.set_value(self.pulse.config[index[0]][index[1]]['rnnoise_control'])

        self.Apply_Rnnoise_Button = self.builder.get_object('apply_rnnoise_button')
        self.Apply_Rnnoise_Button.connect('pressed', self.apply_button, index)

        self.Rnnoise_Popover.popup()

    def apply_button(self, widget, index):
        val = int(self.Rnnoise_Latency_Adjust.get_value())
        self.pulse.config[index[0]][index[1]]['rnnoise_latency'] = val
        val = int(self.Rnnoise_Threshold_Adjust.get_value())
        self.pulse.config[index[0]][index[1]]['rnnoise_control'] = val

        if self.pulse.config[index[0]][index[1]]['use_rnnoise'] == False:
            return
        sink_name = self.pulse.config[index[0]][index[1]]['rnnoise_name']
        command = ''
        command = command + self.pulse.rnnoise(index, sink_name, 'disconnect', 'cmd_only')
        command = command + self.pulse.rnnoise(index, sink_name, 'connect', 'cmd_only')
        # print(command)
        os.popen(command)

