from meexer.schemas.device_schema import DeviceSchema
from meexer.clients.gtk.widgets import common

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class CreateDevice(Gtk.Popover):
    '''
    A widget for creating a new device
    '''
    def __init__(self, device_type, device_list, device_schema: DeviceSchema = None):
        super().__init__()
        main_box = Gtk.VBox(margin=10, hexpand=True)
        self.set_modal(False)
        self.device_list = device_list
        self.device_type = device_type

        if device_type in ('hi', 'a'):
            self.name = common.InputWidget('Nick: ')
            self.device = common.LabeledCombobox('Device: ')
            self.device.combobox.connect("changed", self.device_combo_changed)
            self.ports = common.PortSelector()
            for device in device_list:
                self.device.insert_entry(device['description'])
            main_box.pack_start(self.name, False, False, 10)
            main_box.pack_start(self.device, False, False, 10)
            main_box.pack_start(self.ports, False, False, 10)

        else:

            self.name = common.InputWidget('Name: ')
            self.channel_map = common.LabeledCombobox('Channel Map: ', list(common.CHANNEL_MAPS))
            main_box.pack_start(self.name, False, False, 10)
            main_box.pack_start(self.channel_map, False, False, 10)

        self.create_button = common.IconButton('check-filled')
        self.cancel_button = common.IconButton('cancel')

        self.cancel_button.connect('pressed', self.close_pressed)

        b = Gtk.HBox(halign=Gtk.Align.END)
        b.pack_start(self.cancel_button, False, False, 2)
        b.pack_start(self.create_button, False, False, 2)
        main_box.pack_start(b, False, False, 5)

        self.add(main_box)
        self.show_all()

    def device_combo_changed(self, combo):
        active = combo.get_active()
        device = self.device_list[active]
        self.name.input.set_text(device['description'])
        self.ports.set_ports(device['channel_list'])

    def to_schema(self) -> dict:

        device_type = 'sink' if self.device_type in ('a', 'vi') else 'source'
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'

        if self.device_type in ('b', 'vi'):
            nick = self.name.get_option()
            name = nick
            description = nick
            channel_map = self.channel_map.combobox.get_active_text()
            channel_list = common.CHANNEL_MAPS[channel_map]
            channels = len(channel_list)
            selected_channels = [True] * channels
            volume = [100] * channels

        else:
            selected_device = self.device.combobox.get_active()
            device = self.device_list[selected_device]

            nick = self.name.get_option()
            name = device['name']
            description = device['description']
            selected_channels = self.ports.get_selected()

            channels = 0
            volume = []
            channel_list = []

            # only grab channels that are sellected
            for channel in range(len(selected_channels)):
                if selected_channels[channel] is True:
                    volume.append(device['volume'][channel])
                    channel_list.append(device['channel_list'][channel])
                    channels += 1

        data = {
            'name': name,
            'description': description,
            'nick': nick,
            'channels': channels,
            'channel_list': channel_list,
            'selected_channels': selected_channels,
            'volume': volume,
            'device_type': device_type,
            'device_class': device_class
        }

        return data

    def close_pressed(self, _):
        self.popdown()


if __name__ == '__main__':
    pass
