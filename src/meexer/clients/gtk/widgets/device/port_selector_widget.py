# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class PortSelector(Gtk.Grid):
    '''
    Widget
    '''

    def __init__(self):
        super().__init__()
        self.label = Gtk.Label('Selected ports: ')
        # self.port_grid = Gtk.Grid()
        self.port_box = Gtk.HBox()
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.port_box, 1, 0, 1, 1)

    def set_ports(self, channel_map, selected_channels=None):
        for child in self.port_box.get_children():
            self.port_box.remove(child)

        # for port in channel_map:
        for port in range(len(channel_map)):
            enabled = selected_channels[port] if selected_channels is not None else True
            check = Gtk.CheckButton(label=port, active=enabled)
            self.port_box.pack_start(check, False, False, 0)

        self.port_box.show_all()

    def get_selected(self):
        return [child.get_active() for child in self.port_box.get_children()]
