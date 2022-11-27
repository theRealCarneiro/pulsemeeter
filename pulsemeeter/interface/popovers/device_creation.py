import os
import sys

from pulsemeeter.settings import GLADEFILE
import pulsemeeter.scripts.pmctl as pmctl

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class DeviceCreationPopOver:
    def __init__(self, client, dtype, device_type, device_id=None, edit=False):
        builder = Gtk.Builder()
        try:
            builder.add_objects_from_file(
                os.path.join(GLADEFILE, 'device_creation.glade'),
                ['device_popover']
            )
        except Exception as ex:
            print(f'Error building creation popover!\n{ex}')
            sys.exit(1)

        self.client = client
        self.components = {
            'popup': builder.get_object('device_popover'),
            'trash': builder.get_object('trash'),
            'button': builder.get_object('button'),
            'title': builder.get_object('title'),
        }

        if device_type in ['hi', 'a']:
            self.components = dict(
                self.components, **{
                    'input': builder.get_object('input_hardware'),
                    'combobox': builder.get_object('device_combobox')
                }
            )
        else:
            self.components = dict(
                self.components, **{
                    'input': builder.get_object('input_virtual'),
                    'combobox': builder.get_object('channel_map')
                }
            )

        self.components['virtual']['button'].connect('pressed', self.button_pressed)
        self.components['hardware']['button'].connect('pressed', self.button_pressed)

    def create_popup(self, widget, device_type, relative):
        self.combobox['button'].set_label('Create')
        self.combobox['title'].set_label('Create Device')
        self.combobox['trash'].set_visible(False)

        if device_type in ['hi', 'a']:

            # fill combobox
            devt = 'sinks' if device_type == 'a' else 'sources'
            self.devices = pmctl.list_devices(devt)[device_type]
            for i in range(len(self.devices)):
                desc = self.devices[i]['properties']['device.description']
                self.components[type]['combobox'].append_text(desc)

        self.components[type]['popup'].set_relative_to(relative)
        self.components[type]['popup'].popup()

    # TODO: pactl < 16
    def edit_popup(self, widget, relative, device_type, device_id):

        self.combobox['button'].set_label('Save')
        self.combobox['title'].set_label('Edit Device')
        self.combobox['trash'].set_visible(True)

        device_config = self.client.config[device_type][device_id]
        active_name = device_config['name']
        active_nick = device_config['nick']

        if device_type in ['hi', 'a']:
            input_text = active_nick

            # fill combobox
            devt = 'sinks' if device_type == 'a' else 'sources'
            self.devices = pmctl.list_devices(devt)[device_type]
            for i in range(len(self.devices)):
                name = self.devices[i]['name']
                desc = self.devices[i]['properties']['device.description']
                self.components[type]['combobox'].append_text(desc)
                if active_name == name:
                    self.components[type]['combobox'].set_active(i)
        else:
            input_text = active_name

        self.components[type]['input'].set_text(input_text)
        self.components[type]['popup'].set_relative_to(relative)
        self.components[type]['popup'].popup()

    # TODO:
    def button_pressed(self, button):
        nick = self.components[type]['input'].get_text()
        device = self.devices[self.components[type]['combobox'].get_active()]['name']
        print(nick, device)
