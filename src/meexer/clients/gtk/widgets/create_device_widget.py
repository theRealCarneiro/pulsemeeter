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
            self.nick = common.InputWidget('Nick: ')
            self.device = common.LabeledCombobox('Device: ')
            self.ports = common.PortSelector()
            main_box.pack_start(self.nick, False, False, 10)
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

    def close_pressed(self, _):
        self.popdown()


if __name__ == '__main__':
    pass
