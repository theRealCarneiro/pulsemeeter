import gettext

from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.model.connection_model import pair_match
# from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton

# from pulsemeeter.clients.gtk.adapters.connection_edit_adapter import ConnectionSettingsAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class PortMap(Gtk.Box):

    def __init__(self, connection_model):
        super().__init__()
        self.connection_model = connection_model
        self.checkboxes = {}

    def clear_port_map(self):
        self.checkboxes = {}
        first_child = self.get_first_child()
        if first_child is not None:
            self.remove(first_child)

    def create_port_map(self, input_sel_channels, output_sel_channels) -> list[list[str]]:
        input_ports = [i for i, sel in enumerate(input_sel_channels) if sel]
        output_ports = [i for i, sel in enumerate(output_sel_channels) if sel]

        port_map = [[] for _ in range(len(input_ports))]
        for input_port, output_port in pair_match(input_ports, output_ports):
            port_map[input_port].append(output_port)

        return port_map

    def get_port_map(self):
        port_map = [[] for _ in range(len(self.checkboxes))]
        for input_port, output_port in self.checkboxes:
            check = self.checkboxes[(input_port, output_port)]

            if check.get_active():
                port_map[input_port].append(output_port)

        return port_map

    def _get_port_names(self, device_model) -> list[str]:
        channel_map = device_model.channel_list
        selected_channels = device_model.selected_channels
        j = 0
        ports = []
        for i, sel in enumerate((selected_channels)):
            if not sel:
                continue

            ports.append((i, channel_map[j]))
            j += 1

        return ports

    def create_routing_grid(self, input_device, output_device):
        input_ports = self._get_port_names(input_device)
        output_ports = self._get_port_names(output_device)
        port_map = self.connection_model.port_map
        if not port_map:
            port_map = self.create_port_map(self.connection_model.input_sel_channels,
                                            self.connection_model.output_sel_channels)

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(6)

        # Header row (output port labels)
        for j, output_port in enumerate(output_ports):
            _, output_port_name = output_port
            label = Gtk.Label(label=str(output_port_name), halign=Gtk.Align.CENTER)
            grid.attach(label, j + 1, 0, 1, 1)

        # Rows (input port labels + checkboxes)
        for i, input_port in enumerate(input_ports):
            input_real_id, input_port_name = input_port

            # Input port label
            label = Gtk.Label(label=str(input_port_name))
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 0, i + 1, 1, 1)

            for j, output_port in enumerate(output_ports):
                output_real_id, _ = output_port
                check = Gtk.CheckButton()
                check.set_sensitive(not self.connection_model.auto_ports)
                if output_real_id in port_map[input_real_id]:
                    check.set_active(True)

                grid.attach(check, j + 1, i + 1, 1, 1)
                self.checkboxes[(input_real_id, output_real_id)] = check

        self.append(grid)
