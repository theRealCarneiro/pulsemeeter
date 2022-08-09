# import sys
# import os

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk


class MinimalDevice(Gtk.Grid):
    '''
    A minimal device that only contains a few options,
    so I don't need to do them again
    '''

    def __init__(self, builder, name, mute, volume):
        self.builder = builder

        super(MinimalDevice, self).__init__()

        self.label = builder.get_object('label')
        self.mute = builder.get_object('mute')
        self.adjust = builder.get_object('adjust')
        self.volume = builder.get_object('volume')
        self.vumeter_grid = builder.get_object('vumeter')

        self.label.set_text(name)
        self.mute.set_active(mute)
        self.adjust.set_value(volume)
        self.volume.add_mark(100, Gtk.PositionType.TOP, '')
        self.set_vexpand(True)
        self.set_hexpand(True)

    def insert_output(self, output_type, output_id, name, active):
        button = Gtk.ToggleButton(label=name, active=active)
        self.route_box[output_type].pack_start(button, True, True, 0)
        self.route_dict[output_type][output_id] = button
        return button

    # remove output button
    def remove_output(self, output_type, output_id):
        button = self.route_dict[output_type][output_id]
        self.route_box[output_type].remove(button, True, True, 0)
        del self.route_dict[output_type][output_id]

    # def volume_change(self, slider):
        # val = int(slider.get_value())
        # print(self.device_type, self.device_id, val)
        # if self.device_config['vol'] != val:
            # self.client.volume(self.device_type, self.device_id, val)

    # def connect_click(self, button, event, output_type, output_id):
        # if event.button == 1:
            # state = not button.get_active()
            # print(self.device_type, self.device_id, output_type, output_id, state)
            # # self.client.connect(self.device_type, self.device_id,
                    # # output_type, output_id, state)

        # # right click
        # elif event.button == 3:
            # pass

    # def mute_click(self, button, event):
        # if not event.button == 1:
            # return

        # state = not self.mute.get_active()
        # print(state)
        # # self.client.mute(self.device_type, self.device_id, state)

    # def primary_click(self, button, event):
        # if not event.button == 1:
            # return

        # state = not button.get_active()
        # if state:
            # button.set_sensitive(False)
            # button.set_active(True)
            # self.client.primary(self.device_type, self.device_id)
