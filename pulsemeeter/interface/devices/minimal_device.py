# import sys
# import os

from pulsemeeter.interface.vumeter_widget import Vumeter
from pulsemeeter.interface.popovers.device_creation import DeviceCreationPopOver

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class MinimalDevice(Gtk.Grid):
    '''
    A device that contains a few options,
    so I don't need to do them again
    '''

    def __init__(self, builder, client, device_type, device_id, nick=False):
        self.client = client
        self.builder = builder
        self.device_type = device_type
        self.device_id = device_id
        self.config = client.config
        self.device_config = client.config[device_type][device_id]

        super().__init__()

        self.label = builder.get_object('label')
        self.mute = builder.get_object('mute')
        self.adjust = builder.get_object('adjust')
        self.volume = builder.get_object('volume')
        self.settings = builder.get_object('settings')
        self.vumeter_grid = builder.get_object('vumeter_grid')
        self.vumeter = Vumeter()

        name = self.device_config['nick'] if nick else self.device_config['name']
        self.label.set_text(name)
        self.mute.set_active(self.device_config['mute'])
        self.adjust.set_value(self.device_config['vol'])
        self.volume.add_mark(100, Gtk.PositionType.TOP, '')
        self.vumeter_grid.add(self.vumeter)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.volume.connect('value-changed', self.volume_change)
        self.mute.connect('button_press_event', self.mute_click)

        self.creation_popover = DeviceCreationPopOver(client, device_type, device_id)
        self.settings.connect('pressed', self.creation_popover.edit_popup)

        if self.config['enable_vumeters']:
            self.vumeter.start(self.device_config['name'], device_type)

    def create_route_buttons(self):
        """
        Insert route buttons into device
        """
        for output_type in ['a', 'b']:
            for output_id, output_config in self.config[output_type].items():
                key = 'nick' if output_type == 'a' else 'name'
                name = self.config[output_type][output_id][key]
                active = self.device_config[f'{output_type}{output_id}']['status']
                self.insert_output(output_type, output_id, name, active)

    def insert_output(self, output_type, output_id, name, active):
        button = Gtk.ToggleButton(label=name, active=active)
        self.route_box[output_type].pack_start(button, True, True, 0)
        self.route_dict[output_type][output_id] = button
        button.connect('button_press_event', self.connect_click,
                output_type, output_id)

    def remove_output(self, output_type, output_id):
        button = self.route_dict[output_type][output_id]
        self.route_box[output_type].remove(button)
        del self.route_dict[output_type][output_id]

    def volume_change(self, slider):
        """
        Gets called whenever a volume slider changes
        """
        val = int(slider.get_value())
        self.client.volume(self.device_type, self.device_id, val)

    def connect_click(self, button, event, output_type, output_id):
        """
        Gets called whenever a route button is clicked
        """

        if event.button == 1:
            state = not button.get_active()
            self.client.connect(self.device_type, self.device_id,
                    output_type, output_id, state)

        # right click
        # elif event.button == 3:
            # pass

    def mute_click(self, button, event):
        """
        Gets called whenever a mute button is clicked
        """
        if not event.button == 1:
            return

        state = not self.mute.get_active()
        self.client.mute(self.device_type, self.device_id, state)

    def primary_click(self, button, event):
        """
        Gets called whenever a primary button is clicked
        """
        if not event.button == 1:
            return

        button.set_sensitive(False)
        button.set_active(True)
        self.client.primary(self.device_type, self.device_id)

    def rnnoise_click(self, button, event):
        """
        Gets called whenever a rnnoise button is clicked
        """
        if event.button == 1:
            state = not button.get_active()
            self.client.rnnoise(self.device_id, state)

    def eq_click(self, button, event):
        """
        Gets called whenever an eq button is clicked
        """
        if event.button == 1:
            state = not button.get_active()
            self.client.eq(self.device_type, self.device_id, state)
