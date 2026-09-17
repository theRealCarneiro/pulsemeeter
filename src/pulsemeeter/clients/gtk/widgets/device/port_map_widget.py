import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext

PORT_NAME_PREFIXES = ('playback_', 'capture_', 'monitor_', 'input_', 'output_')


def port_label(port_name: str) -> str:
    '''
    Strip the pipewire direction prefix off a port name for display.
    '''
    for prefix in PORT_NAME_PREFIXES:
        if port_name.startswith(prefix):
            return port_name[len(prefix):]

    return port_name


class PortMap(Gtk.Box):

    def __init__(self, connection_model):
        super().__init__()
        self.connection_model = connection_model
        self.checkboxes = {}
        self.map_rows = 0
        self.rendered_positions = []

    def clear_port_map(self):
        self.checkboxes = {}
        self.map_rows = 0
        self.rendered_positions = []
        first_child = self.get_first_child()
        if first_child is not None:
            self.remove(first_child)

    def get_port_map(self):
        '''
        Read the checkbox grid back into a port_map.
        '''
        active_pairs = [key for key, check in self.checkboxes.items() if check.get_active()]

        return self.connection_model.merge_port_map(
            active_pairs, self.rendered_positions, self.map_rows
        )

    def create_routing_grid(self, input_device, output_device, input_ports, output_ports):
        '''
        Build the checkbox grid for a connection.
        '''
        input_sel_channels = input_device.get_selected_channel_list()
        output_sel_channels = output_device.get_selected_channel_list()

        rows, cols, checked = self.connection_model.routing_grid(
            input_ports, output_ports, input_sel_channels, output_sel_channels
        )

        self.map_rows = len(input_sel_channels)
        self.rendered_positions = [position for position, _unused in rows]

        if not rows or not cols:
            self.show_message(_('No ports available'))
            return

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(6)

        # Header row (output port labels)
        for column, (_unused, output_name) in enumerate(cols):
            label = Gtk.Label(label=port_label(output_name), halign=Gtk.Align.CENTER)
            grid.attach(label, column + 1, 0, 1, 1)

        # Rows (input port labels + checkboxes)
        for row, (position, input_name) in enumerate(rows):
            label = Gtk.Label(label=port_label(input_name))
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 0, row + 1, 1, 1)

            for column, (output_channel, _unused) in enumerate(cols):
                check = Gtk.CheckButton(active=(position, output_channel) in checked)
                check.set_sensitive(not self.connection_model.auto_ports)

                grid.attach(check, column + 1, row + 1, 1, 1)
                self.checkboxes[(position, output_channel)] = check

        self.append(grid)

    def show_message(self, text: str):
        self.append(Gtk.Label(label=text, halign=Gtk.Align.CENTER))

    def show_unavailable(self):
        self.show_message(_('Could not read device ports'))
