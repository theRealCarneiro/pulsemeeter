import os
import sys
import logging
import traceback
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk

CHANNELS = [
    'MONO',
    'FL FR',
    'FL FR RL RR',
    'FL FR FC RL RR',
    'FL FR FC LFE RL RR',
    'FL FR FC RL RR SL SR',
    'FL FR FC LFE RL RR SL SR'
]

LOG = logging.getLogger("generic")


class PortMapPopover():
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
            LOG.error(f'could not build main window!\n{traceback.format_exc()}')
            sys.exit(1)

        output = self.output_type + self.output_id

        input_name = self.client.config[input_type][input_id]['name']
        output_name = self.client.config[output_type][output_id]['name']

        # exit if there's no device
        if input_name != '' and output_name != '':

            self.toggle_grouping_setting = self.builder.get_object('portselect_grouping_toggle')
            self.toggle_grouping_setting.set_active(client.config[input_type][input_id][output]['auto_ports'])
            self.toggle_grouping_setting.set_active(client.config[self.input_type][self.input_id][output]['auto_ports'])
            self.toggle_grouping_setting.connect('toggled', self.toggle_grouping)

            self.apply_port_button = self.builder.get_object('apply_port_button')
            self.apply_port_button.connect('pressed', self.apply)

            self.channel_box = self.builder.get_object('channel_box')
            self.channel_box.set_sensitive(not client.config[self.input_type][self.input_id][output]['auto_ports'])

            self.create_port_list()

            port_popover = self.builder.get_object('portselect_popover')
            port_popover.set_relative_to(button)
            port_popover.popup()

    def create_port_list(self):
        input_config = self.client.config[self.input_type][self.input_id]
        output_config = self.client.config[self.output_type][self.output_id]

        output = f'{self.output_type}{self.output_id}'
        output_ports = output_config['channels']
        input_ports = input_config['channels']

        port_map = input_config[output]['port_map']

        # clear channel box
        for i in self.channel_box:
            self.channel_box.remove(i)

        icount = 0
        self.button_list = [[None for j in range(output_ports)] for i in range(input_ports)]
        for iport in range(input_ports):
            ocount = 0
            if ('selected_channels' in input_config and
                    input_config['selected_channels'][iport] is False):
                icount += 1
                continue

            hbox = Gtk.HBox(spacing=1)
            label = Gtk.Label(label=iport + 1)
            label.set_size_request(50, 0)
            hbox.pack_start(label, True, True, 0)
            for oport in range(output_ports):
                if (len(output_config['selected_channels']) > 0 and
                        output_config['selected_channels'][oport] is False):
                    ocount += 1
                    continue
                button = Gtk.CheckButton(label=oport + 1)

                # set button as active or not
                if (len(port_map) != 0 and oport in port_map[iport]) or (
                        (self.toggle_grouping_setting.get_active() is True and icount == ocount)):
                    button.set_active(True)

                self.button_list[iport][oport] = button
                hbox.pack_start(button, True, True, 0)
                ocount += 1
            self.channel_box.pack_start(hbox, True, True, 0)
            icount += 1

        self.channel_box.show_all()

    def apply(self, widget):

        status = self.toggle_grouping_setting.get_active()
        self.client.set_auto_ports(self.input_type, self.input_id, self.output, status)

        port_map = []

        for iport in range(len(self.button_list)):
            ports = []
            for oport in range(len(self.button_list[iport])):

                button = self.button_list[iport][oport]
                if button is not None:
                    port = int(button.get_label()) - 1
                    if button.get_active() is True:
                        ports.append(port)

            port_map.append(ports)

        # print(port_map)
        self.client.set_port_map(self.input_type, self.input_id, self.output, port_map)

    def toggle_grouping(self, widget):
        self.client.config[self.input_type][self.input_id][self.output]['auto_ports'] = widget.get_active()
        if widget.get_active() is False:
            self.channel_box.set_sensitive(True)
            self.create_port_list()
        else:
            ic = 0
            for button_list in self.button_list:
                oc = 0
                for button in button_list:
                    if button is not None:
                        button.set_active(True if ic == oc else False)
                        oc += 1
                ic += 1
            self.channel_box.set_sensitive(False)