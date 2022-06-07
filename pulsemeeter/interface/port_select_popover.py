import os
import sys
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk

CHANNELS = {
    '1': 'MONO',
    '2': 'FL FR',
    '4': 'FL FR RL RR',
    '5': 'FL FR FC RL RR',
    '5.1': 'FL FR FC LFE RL RR',
    '7': 'FL FR FC RL RR SL SR',
    '7.1': 'FL FR FC LFE RL RR SL SR'
}


class PortSelectPopover():
    def __init__(self, button, client, input_type, input_id, output_type, output_id):

        self.builder = Gtk.Builder()
        self.layout = client.config['layout']
        self.client = client

        self.input_type = input_type
        self.input_id = input_id
        self.output_type = output_type
        self.output_id = output_id
        self.output = f'{output_type}{output_id}'

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

        output = self.output_type + self.output_id

        self.port_select_popover = self.builder.get_object('portselect_popover')
        self.port_select_popover.set_relative_to(button)

        self.toggle_grouping_setting = self.builder.get_object('portselect_grouping_toggle')
        self.toggle_grouping_setting.set_active(client.config[self.input_type][self.input_id][output]['auto_ports'])
        self.toggle_grouping_setting.connect('toggled', self.toggle_grouping)

        self.apply_port_button = self.builder.get_object('apply_port_button')
        self.apply_port_button.connect('pressed', self.apply)

        self.channel_box = self.builder.get_object('channel_box')
        self.channel_box.set_sensitive(not client.config[self.input_type][self.input_id][output]['auto_ports'])

        self.create_port_list()

        self.port_select_popover.popup()

    def create_port_list(self, default=False):
        input_config = self.client.config[self.input_type][self.input_id]
        output_config = self.client.config[self.output_type][self.output_id]

        output = f'{self.output_type}{self.output_id}'
        output_port_name = 'playback' if self.output_type == 'a' else 'input'
        input_port_name = 'monitor' if self.input_type == 'vi' else 'capture'
        output_ports = CHANNELS[output_config['channel_map']].split(' ')
        input_ports = CHANNELS[input_config['channel_map']].split(' ')

        port_map = input_config[output]['port_map']

        # clear channel box
        for i in self.channel_box:
            self.channel_box.remove(i)

        icount = 0
        self.button_list = {}
        for iport in input_ports:
            hbox = Gtk.HBox(spacing=1)
            label = Gtk.Label(label=f'{iport}:')
            label.set_size_request(50, 0)
            hbox.pack_start(label, True, True, 0)
            self.button_list[f'{input_port_name}_{iport}'] = {}
            ocount = 0
            for oport in output_ports:
                button = Gtk.CheckButton(label=oport)

                # set button as active or not
                if f'{output_port_name}_{oport}' in port_map[f'{input_port_name}_{iport}'] or (
                        default is True and icount == ocount):
                    button.set_active(True)

                self.button_list[f'{input_port_name}_{iport}'][f'{output_port_name}_{oport}'] = button
                hbox.pack_start(button, True, True, 0)
                ocount += 1
            self.channel_box.pack_start(hbox, True, True, 0)

        self.channel_box.show_all()

    def apply(self, widget):
        port_map = {}

        if self.toggle_grouping_setting.get_active() is True:
            pass

        for iport in self.button_list:
            port_map[iport] = []
            for oport in self.button_list[iport]:

                if self.button_list[iport][oport].get_active() is True:
                    port_map[iport].append(oport)

        self.client.set_port_map(self.input_type, self.input_id, self.output, port_map)
        print(port_map)

    def toggle_grouping(self, widget):
        self.client.config[self.input_type][self.input_id][self.output]['auto_ports'] = widget.get_active()
        if widget.get_active() is False:
            self.channel_box.set_sensitive(True)
            self.create_port_list()
        else:
            ic = 0
            for iport in self.button_list:
                oc = 0
                for oport in self.button_list[iport]:
                    self.button_list[iport][oport].set_active(True if ic == oc else False)
                    oc += 1
                ic += 1
            self.channel_box.set_sensitive(False)
