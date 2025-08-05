import gettext

from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.model.connection_model import pair_match
# from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.device.port_map_widget import PortMap

# from pulsemeeter.clients.gtk.adapters.connection_edit_adapter import ConnectionSettingsAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionSettingsPopup(Gtk.Popover):

    def __init__(self, connection_model: ConnectionModel = None):

        super().__init__()
        # self.get_accessible().set_name(_('Connection Settings'))
        self.connection_model = connection_model

        # create widgets
        self.auto_ports_check = Gtk.CheckButton(label=_("Auto ports"), )
        # self.confirm_button = IconButton('object-select-symbolic')
        self.confirm_button = Gtk.Button(label=_('Apply'))
        # self.cancel_button = IconButton('window-close-symbolic')
        self.port_map_widget = PortMap(connection_model)
        # self.button_grid, self.checkboxes = self.create_routing_grid(connection_model)

        # self.auto_ports_check.set_active(connection_model.auto_ports)

        # connect events
        # self.cancel_button.connect('clicked', self.close_pressed)
        self.auto_ports_check.connect('toggled', self.change_checkbox_active)

        # add widgets to grid
        button_box = Gtk.Box(halign=Gtk.Align.END)
        # button_box.append(self.cancel_button)
        button_box.append(self.confirm_button)

        main_box = Gtk.Box(hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.auto_ports_check)
        main_box.append(self.port_map_widget)
        main_box.append(button_box)

        # self.cancel_button.get_accessible().set_name(_("Cancel"))
        # self.confirm_button.get_accessible().set_name(_("Create device"))

        # self.set_modal(False)
        self.set_child(main_box)
        # self.show_all()
        # self.name_widget.input.grab_focus()

    def fill_settings(self):
        self.auto_ports_check.set_active(self.connection_model.auto_ports)
        # self.port_map_widget.fill_settings()

    def change_checkbox_active(self, widget):
        for checkbox in self.port_map_widget.checkboxes.values():
            checkbox.set_sensitive(not widget.get_active())

    def get_port_map(self):
        if self.auto_ports_check.get_active():
            return []

        input_sel_channels = self.connection_model.input_sel_channels
        output_sel_channels = self.connection_model.output_sel_channels

        input_ports = [i for i, sel in enumerate(input_sel_channels) if sel]
        output_ports = [i for i, sel in enumerate(output_sel_channels) if sel]

        port_map = []

        for in_rel_idx, in_abs in enumerate(input_ports):
            output_connections = []

            for out_rel_idx, out_abs in enumerate(output_ports):
                check = self.checkboxes.get((in_abs, out_abs))
                if check and check.get_active():
                    output_connections.append(out_rel_idx)

            port_map.append(output_connections)

        return port_map

    def get_connection_model(self):
        model = self.connection_model.copy()
        model.auto_ports = self.auto_ports_check.get_active()
        model.port_map = [] if model.auto_ports else self.port_map_widget.get_port_map()
        return model

    def create_routing_grid(self, connection_model):
        input_sel_channels = connection_model.input_sel_channels
        output_sel_channels = connection_model.output_sel_channels
        port_map = connection_model.port_map

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(6)

        # Map selected indexes to absolute indexes
        input_ports = [i for i, sel in enumerate(input_sel_channels) if sel]
        output_ports = [i for i, sel in enumerate(output_sel_channels) if sel]

        if not port_map:
            port_map = [[] for _ in range(len(input_ports))]
            for input_port, output_port in pair_match(input_ports, output_ports):
                port_map[input_port].append(output_port)

        checkboxes = {}

        # Header row (output port labels)
        for j, out_abs in enumerate(output_ports):
            label = Gtk.Label(label=str(out_abs))
            label.set_halign(Gtk.Align.CENTER)
            grid.attach(label, j + 1, 0, 1, 1)

        # Rows (input port labels + checkboxes)
        for i, in_abs in enumerate(input_ports):
            # Input label
            label = Gtk.Label(label=str(in_abs))
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 0, i + 1, 1, 1)

            # Get connections for this input, if port_map is not empty
            connected_outputs = []
            if port_map and i < len(port_map):
                connected_outputs = port_map[i]

            for j, out_abs in enumerate(output_ports):
                check = Gtk.CheckButton()

                # Determine if this connection exists in port_map
                if j in connected_outputs:
                    check.set_active(True)

                check.set_sensitive(not connection_model.auto_ports)

                grid.attach(check, j + 1, i + 1, 1, 1)

                checkboxes[(in_abs, out_abs)] = check

        return grid, checkboxes
