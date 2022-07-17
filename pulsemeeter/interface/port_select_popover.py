import os
import sys
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


class PortSelectPopover():
    def __init__(self, button, client, device_type, device_id):

        self.builder = Gtk.Builder()
        self.layout = client.config['layout']
        self.client = client

        self.device_type = device_type
        self.device_id = device_id
        self.device_config = self.client.config[device_type][device_id]

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
                [
                    'portselect_popover',
                    'portselect_grouping_toggle',
                    'portselect_grouped_ports',
                    'portselect_right_ports',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        device_name = self.device_config['name']
        if device_name != '':
            self.port_select_popover = self.builder.get_object('portselect_popover')
            self.port_select_popover.set_relative_to(button)

            toggle_grouping_setting = self.builder.get_object('portselect_grouping_toggle')
            toggle_grouping_setting.set_no_show_all(True)
            toggle_grouping_setting.set_visible(False)

            apply_port_button = self.builder.get_object('apply_port_button')
            apply_port_button.connect('pressed', self.apply)

            self.channel_box = self.builder.get_object('channel_box')
            # self.channel_box.set_sensitive(not client.config[self.input_type][self.input_id][output]['auto_ports'])

            self.create_port_list()

            self.port_select_popover.popup()

    def create_port_list(self):
        device_type = self.device_type
        device_id = self.device_id
        device_config = self.client.config[device_type][device_id]

        device_ports = device_config['channels']
        if 'selected_channels' not in device_config:
            print(device_type, device_id)
        selected_ports = device_config['selected_channels']

        if len(selected_ports) == 0:
            selected_ports = None

        # clear channel box
        for i in self.channel_box:
            self.channel_box.remove(i)

        self.button_list = []
        hbox = Gtk.HBox(spacing=1)
        for port in range(device_ports):

            button = Gtk.CheckButton(label=port + 1)

            # set button as active or not
            if (selected_ports is None or selected_ports[port] is True):
                button.set_active(True)

            hbox.pack_start(button, True, True, 0)
            self.button_list.append(button)

        self.channel_box.pack_start(hbox, True, True, 0)

        self.channel_box.show_all()

    def apply(self, widget):

        status = self.toggle_grouping_setting.get_active()
        self.client.set_auto_ports(self.input_type, self.input_id, self.output, status)

        ports = [button.get_active() for button in self.button_list]

        self.client.set_port_map(self.input_type, self.input_id, self.output, ports)

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
                    button.set_active(True if ic == oc else False)
                    oc += 1
                ic += 1
            self.channel_box.set_sensitive(False)
