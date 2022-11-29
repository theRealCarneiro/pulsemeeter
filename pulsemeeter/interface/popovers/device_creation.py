import os
import sys
import json
import logging

from pulsemeeter.settings import LAYOUT_DIR
import pulsemeeter.scripts.pmctl as pmctl

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk

LOG = logging.getLogger("generic")


class DeviceCreationPopOver:
    def __init__(self, client, device_type, device_id=None):
        builder = Gtk.Builder()
        self.config = client.config
        self.dtype = 'hardware' if device_type in ['hi', 'a'] else 'virtual'
        self.device_type = device_type
        self.device_id = device_id

        try:
            builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{client.config["layout"]}/{self.dtype}_settings.glade'),
                ['device_popover']
            )
        except Exception as ex:
            print(f'Error building creation popover!\n{ex}')
            sys.exit(1)

        self.client = client

        self.popup = builder.get_object('device_popover')
        self.trash = builder.get_object('trash')
        self.button = builder.get_object('button')
        self.title = builder.get_object('title')
        self.input = builder.get_object('input')
        self.channel_box = builder.get_object('channel_box')
        self.device_combobox = builder.get_object('device_combobox')
        self.channel_map = builder.get_object('channel_map_combobox')
        self.external = builder.get_object('external')

        if self.dtype == 'hardware':
            self.device_combobox.connect('changed', self.device_combo_change)
        self.button.connect('pressed', self.button_pressed)
        self.trash.connect('pressed', self.remove_device)

    def fill_devices_combobox(self):
        self.device_combobox.remove_all()
        if self.device_id is not None:
            active_name = self.config[self.device_type][self.device_id]['name']

        devt = 'sinks' if self.device_type == 'a' else 'sources'

        # get device list
        self.devices = pmctl.list_devices(devt)[self.device_type]
        for i in range(len(self.devices)):
            name = self.devices[i]['name']
            desc = self.devices[i]['properties']['device.description']
            self.device_combobox.append_text(desc)

            # set active if editing
            if self.device_id is not None and active_name == name:
                self.device_combobox.set_active(i)

        self.active_index = i

    def create_port_list(self):
        device_type = self.device_type
        device_id = self.device_id
        if device_id is None:
            channels = self.devices[self.active_index]['properties']['audio.channels']
            selected_ports = None
            device_ports = int(channels)
        else:
            device_config = self.client.config[device_type][device_id]

            device_ports = device_config['channels']
            if 'selected_channels' not in device_config:
                LOG.debug(f'{device_type} {device_id}')
            selected_ports = device_config['selected_channels']

            if len(selected_ports) == 0:
                selected_ports = None

        # clear channel box
        for i in self.channel_box:
            self.channel_box.remove(i)

        self.button_list = []
        hbox = Gtk.HBox(spacing=1)

        # for each port
        for port in range(device_ports):

            button = Gtk.CheckButton(label=port + 1)

            # set button as active or not
            if (selected_ports is None or selected_ports[port] is True):
                button.set_active(True)

            hbox.pack_start(button, True, True, 0)
            self.button_list.append(button)

        self.channel_box.pack_start(hbox, True, True, 0)

        self.channel_box.show_all()

    def device_combo_change(self, widget):
        self.create_port_list()

    def create_popup(self, widget):
        self.button.set_label('Create')
        self.title.set_label('Create Device')
        self.trash.set_visible(False)

        if self.dtype == 'hardware':
            self.fill_devices_combobox()
            # self.create_port_list()

        self.popup.set_relative_to(widget)
        self.popup.popup()

    def edit_popup(self, widget):

        self.button.set_label('Save')
        self.title.set_label('Edit Device')
        self.trash.set_visible(True)

        device_config = self.client.config[self.device_type][self.device_id]

        if self.dtype == 'hardware':
            input_text = device_config['nick']
            self.fill_devices_combobox()
            self.create_port_list()
        else:
            input_text = device_config['name']
            channels = device_config['channels']

            # index of channel map in combobox
            tmp = [None, 1, 0, None, 2, 3, None, None, 4]
            self.channel_map.set_active(tmp[channels])
            self.external.set_active(device_config['external'])

        self.input.set_text(input_text)
        self.popup.set_relative_to(widget)
        self.popup.popup()

    # TODO: send to client
    def button_pressed(self, button):
        if self.dtype == 'hardware':
            active_device = self.devices[self.device_combobox.get_active()]
            device = {
                'nick': self.input.get_text(),
                'device': active_device['name'],
                'description': active_device['properties']['device.description'],
                'channels': active_device['properties']['audio.channels'],
                'selected_channels': [button.get_active() for button in self.button_list]
            }
        else:
            name = self.input.get_text()
            channel_map = self.channel_map.get_active()

            # number of channels per channel map
            tmp = [2, 1, 4, 5, 8]
            external = self.external.get_active()
            device = {
                'name': name,
                'channels': tmp[channel_map],
                'external': external
            }
        if self.device_id is None:
            self.client.create_device(self.device_type, device)
        else:
            self.client.edit_device(self.device_type, self.device_id, device)

    def remove_device(self, button):
        self.client.remove_device(self.device_type, self.device_id)
