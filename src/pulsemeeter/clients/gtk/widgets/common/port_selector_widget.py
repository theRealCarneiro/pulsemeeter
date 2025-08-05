import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class PortSelector(Gtk.Grid):
    '''
    Widget
    '''

    def __init__(self):
        super().__init__()
        self.label = Gtk.Label(label=_('Selected ports: '))
        self.port_box = Gtk.Box()
        # self.port_box.get_accessible().set_name(_('Selected ports'))
        # self.port_box.get_accessible().set_role(Atk.Role.PANEL)
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.port_box, 1, 0, 1, 1)

    def set_ports(self, channel_map, selected_channels=None):
        for child in list(self.port_box):
            self.port_box.remove(child)

        # for port in channel_map:
        for port, port_name in enumerate(channel_map):
            enabled = selected_channels[port] if selected_channels is not None else True
            check = Gtk.CheckButton(label=port_name, active=enabled)
            self.port_box.append(check)

            # check.get_accessible().set_name(f"{port} port")
            check.set_tooltip_text(_("Toggle the port ") + str(port))

        # self.port_box.show_all()

    def get_selected(self):
        return [child.get_active() for child in self.port_box]
