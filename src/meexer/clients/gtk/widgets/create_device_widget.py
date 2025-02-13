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
    def __init__(self, device_type, device_schema: DeviceSchema = None):
        super().__init__()
        main_box = Gtk.VBox(margin=10, hexpand=True)

        if device_type in ('hi', 'a'):
            self.name = common.InputWidget('Nick: ')
            self.device = common.LabeledCombobox('Device: ')
            self.ports = common.PortSelector()
            main_box.pack_start(self.name, False, False, 10)
            main_box.pack_start(self.device, False, False, 10)
            main_box.pack_start(self.ports, False, False, 10)

        else:

            self.name = common.InputWidget('Name: ')
            self.channel_map = common.LabeledCombobox('Channel Map: ')
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

    def create_pressed(self, _):
        nick_text = self.nick.get_option()
        # device_text = self.device.get_active_text() or ""
        ports_data = [0, 1]
        # ports_data = self.ports.get_selected_ports()  # e.g., [0, 1]
        channels = len(ports_data) if ports_data else 2

        new_device = DeviceSchema(
            name=nick_text,
            # description=nick_text,
            channels=channels,
            channel_list=ports_data,
            selected_channels=[True] * channels,
            device_type='sink',  # Adjust as needed for hardware
            device_class='hardware',
            mute=False,
            volume=[100] * channels  # Assuming volume is a percentage
        )

    def close_pressed(self, _):
        self.popdown()


if __name__ == '__main__':
    pass
