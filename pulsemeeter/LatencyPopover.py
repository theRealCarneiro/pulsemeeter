from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class Latency_Popup():
    def __init__(self, button, pulse, config, gladefile, index):

        self.config = config
        self.builder = Gtk.Builder()

        try:
            self.builder.add_objects_from_file(
                gladefile,
                [
                    'Latency_Popover',
                    'Latency_Adjust',
                    'Apply_Latency_Button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.Latency_Popover = self.builder.get_object('Latency_Popover')
        self.Latency_Popover.set_relative_to(button)

        self.Latency_Adjust = self.builder.get_object('Latency_Adjust')
        self.Latency_Adjust.set_value(self.config[index[0]][index[1]][index[2] + '_latency'])
        # self.Latency_Adjust.connect('value_changed', self.latency_adjust, [index[0], index[1], index[2] + '_latency'])
        self.Apply_Latency_Button = self.builder.get_object('Apply_Latency_Button')
        self.Apply_Latency_Button.connect('pressed', self.apply_latency, index, pulse)


        self.Latency_Popover.popup()

    # def latency_adjust(self, widget, index):
        # val = int(widget.get_value())
        # self.config[index[0]][index[1]][index[2]] = val

    def apply_latency(self, widget, index, pulse):
        val = int(self.Latency_Adjust.get_value())
        self.config[index[0]][index[1]][index[2] + '_latency'] = val
        if self.config[index[0]][index[1]][index[2]] == False:
            return
        dev = list(index[2])
        command = ''
        command = command + pulse.connect(self.config, 'disconnect', [index[0], index[1]], dev, 'init')
        command = command + pulse.connect(self.config, 'connect', [index[0], index[1]], dev, 'init')
        # print(command)
        os.popen(command)

