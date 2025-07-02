import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Atk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class PortSelector(Gtk.Grid):
    '''
    Widget
    '''

    def __init__(self):
        super().__init__()
        self.label = Gtk.Label(_('Selected ports: '))
        self.port_box = Gtk.HBox()
        self.port_box.get_accessible().set_name(_('Selected ports'))
        self.port_box.get_accessible().set_role(Atk.Role.PANEL)
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

            check.get_accessible().set_name(f"{port} port")
            check.set_tooltip_text(_("Enable or disable the port ") + str(port))

        self.port_box.show_all()

    def get_selected(self):
        return [child.get_active() for child in self.port_box.get_children()]
