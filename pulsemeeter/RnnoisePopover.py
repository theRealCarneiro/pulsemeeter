from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class Rnnoise_Popup():
    def __init__(self, button, config, pulse, gladefile, index):

        self.config = config
        self.builder = Gtk.Builder()

        try:
            self.builder.add_objects_from_file(
                gladefile,
                [
                    'Noisetorch_Popover',
                    'Noisetorch_Latency_Adjust',
                    'Noisetorch_Threshold_Adjust',
                    'Apply_Noisetorch_Button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.Noisetorch_Popover = self.builder.get_object('Noisetorch_Popover')
        self.Noisetorch_Popover.set_relative_to(button)

        self.Noisetorch_Latency_Adjust = self.builder.get_object('Noisetorch_Latency_Adjust')
        self.Noisetorch_Latency_Adjust.set_value(self.config[index[0]][index[1]]['rnnoise_latency'])
        # self.Noisetorch_Latency_Adjust.connect('value_changed', self.latency_adjust, [index[0], index[1]])

        self.Noisetorch_Threshold_Adjust = self.builder.get_object('Noisetorch_Threshold_Adjust')
        self.Noisetorch_Threshold_Adjust.set_value(self.config[index[0]][index[1]]['rnnoise_control'])
        # self.Noisetorch_Threshold_Adjust.connect('value_changed', self.threshold_adjust, [index[0], index[1]])

        self.Apply_Noisetorch_Button = self.builder.get_object('Apply_Noisetorch_Button')
        self.Apply_Noisetorch_Button.connect('pressed', self.apply_button, index, pulse)

        self.Noisetorch_Popover.popup()

    # def latency_adjust(self, widget, index):
        # val = int(widget.get_value())
        # self.config[index[0]][index[1]]['rnnoise_latency'] = val

    # def threshold_adjust(self, widget, index):
        # val = int(widget.get_value())
        # self.config[index[0]][index[1]]['rnnoise_control'] = val

    def apply_button(self, widget, index, pulse):
        val = int(self.Noisetorch_Latency_Adjust.get_value())
        self.config[index[0]][index[1]]['rnnoise_latency'] = val
        val = int(self.Noisetorch_Threshold_Adjust.get_value())
        self.config[index[0]][index[1]]['rnnoise_control'] = val

        if self.config[index[0]][index[1]]['use_rnnoise'] == False:
            return
        sink_name = self.config[index[0]][index[1]]['rnnoise_name']
        command = ''
        command = command + pulse.rnnoise(self.config, index, sink_name, 'disconnect', 'cmd_only')
        command = command + pulse.rnnoise(self.config, index, sink_name, 'connect', 'cmd_only')
        # print(command)
        os.popen(command)

