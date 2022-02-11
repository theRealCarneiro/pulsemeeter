import os
import sys
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class PortSelectPopover():
    def __init__(self, button, pulse, index):

        self.config = pulse.config
        self.builder = Gtk.Builder()
        self.layout = pulse.config['layout']
        self.pulse = pulse
        self.index = index

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
                [
                    'portselect_popover',
                    'portselect_grouping_toggle',
                    'portselect_grouped_ports',
                    'portselect_notebook',
                    'portselect_left_ports',
                    'portselect_right_ports',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        output = f'{self.index[2][0]}{self.index[2][1]}'
        jack_ports = f'{output}_jack_map'
        port_group = f'{output}_port_group'
        if port_group not in self.pulse.config[self.index[0]][self.index[1]]:
            self.pulse.config[self.index[0]][self.index[1]][port_group] = True

        self.apply_port_button = self.builder.get_object('apply_port_button')
        self.apply_port_button.connect('pressed', self.apply)
        self.PortSelect_Popover = self.builder.get_object('portselect_popover')
        self.PortSelect_Popover.set_relative_to(button)
        self.channel_box = self.builder.get_object('channel_box')
        self.toggle_grouping_setting = self.builder.get_object('portselect_grouping_toggle')
        self.create_port_list()
        self.toggle_grouping_setting.set_active(self.pulse.config[index[0]][index[1]][port_group])
        self.channel_box.set_sensitive(not self.pulse.config[index[0]][index[1]][port_group])
        self.toggle_grouping_setting.connect('toggled', self.toggle_grouping, index, pulse)

        self.PortSelect_Popover.popup()

    def create_port_list(self, default=False):
        channel_group = self.pulse.config[self.index[2][0]][self.index[2][1]]['name']
        if self.index[2][0] == 'a':
            ports = self.pulse.config['jack']['output_groups'][channel_group]
        else:
            ports = self.pulse.config['b'][self.index[2][1:]]['channel_map']
        port_num = len(ports)
        sink_channel_num = self.pulse.config[self.index[0]][self.index[1]]['channels']
        if self.index[0] != 'hi':
            sink_channel_map = self.pulse.config[self.index[0]][self.index[1]]['channel_map']
        else:
            group = self.pulse.config[self.index[0]][self.index[1]]['name']
            sink_channel_map = self.pulse.config['jack']['input_groups'][group]
        if len(sink_channel_map) == 0:
            sink_channel_map = self.pulse.channels[:sink_channel_num]

        output = self.index[2]
        jack_ports = f'{output}_jack_map'
        port_group = f'{output}_port_group'
        for i in self.channel_box:
            self.channel_box.remove(i)
        self.button_list = {}
        for channel in sink_channel_map:
            hbox = Gtk.HBox(spacing=5)
            label = Gtk.Label(label=channel)
            label.set_size_request(100,0)
            hbox.pack_start(label, True, True, 0)
            count = 0
            self.button_list[channel] = {}
            for i in ports:
                self.button_list[channel][i] = Gtk.CheckButton(label=i)
                if self.pulse.config[self.index[0]][self.index[1]][port_group] == True or default == True:
                    if count == sink_channel_map.index(channel):
                        self.button_list[channel][i].set_active(True)
                else:
                    if jack_ports not in self.pulse.config[self.index[0]][self.index[1]]:
                        self.pulse.config[self.index[0]][self.index[1]][jack_ports] = {}
                    if channel in self.pulse.config[self.index[0]][self.index[1]][jack_ports]:
                        # print(self.pulse.config[self.index[0]][self.index[1]][jack_ports][channel])
                        if i in self.pulse.config[self.index[0]][self.index[1]][jack_ports][channel]:
                            self.button_list[channel][i].set_active(True)
                hbox.pack_start(self.button_list[channel][i], True, True, 0)
                count += 1
            self.channel_box.pack_start(hbox, True, True, 0)

        self.channel_box.show_all()

    def apply(self, widget):
        jack_ports = f'{self.index[2][0]}{self.index[2][1]}_jack_map'
        if self.toggle_grouping_setting.get_active() == True:
            try:
                del self.pulse.config[self.index[0]][self.index[1]][jack_ports]
            except:
                pass
            return

        self.pulse.config[self.index[0]][self.index[1]][jack_ports] = {}
        for source_port in self.button_list:
            self.pulse.config[self.index[0]][self.index[1]][jack_ports][source_port] = []
            for system_port in self.button_list[source_port]:
                if self.button_list[source_port][system_port].get_active() == True:
                    self.pulse.config[self.index[0]][self.index[1]][jack_ports][source_port].append(system_port)
        # self.button_list.clear()


    def toggle_grouping(self, widget, index, pulse):
        self.pulse.config[index[0]][index[1]][f'{index[2][0]}{index[2][1]}_port_group'] = widget.get_active()
        if widget.get_active() == False:
            self.channel_box.set_sensitive(True)
            self.create_port_list()
        else:
            self.create_port_list(default=True)
            self.channel_box.set_sensitive(False)
