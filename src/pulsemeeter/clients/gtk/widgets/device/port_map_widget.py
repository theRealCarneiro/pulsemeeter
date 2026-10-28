import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext

PORT_NAME_PREFIXES = ('playback_', 'capture_', 'monitor_', 'input_', 'output_')
COLUMN_SPACING = 6


def port_label(port_name: str) -> str:
    '''
    Strip the pipewire direction prefix off a port name for display.
    '''
    for prefix in PORT_NAME_PREFIXES:
        if port_name.startswith(prefix):
            return port_name[len(prefix):]

    return port_name


def axis_marker(text: str) -> Gtk.Label:
    label = Gtk.Label(halign=Gtk.Align.CENTER)
    label.set_markup(f'<small>{GLib.markup_escape_text(text)}</small>')
    label.add_css_class('dim-label')

    return label


class PortMap(Gtk.Box):

    __gsignals__ = {
        # a checkbox was clicked, read the new map with get_port_map
        'changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

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
        input_channels = input_device.get_selected_channels(input_ports)
        output_channels = output_device.get_selected_channels(output_ports)

        rows, cols, checked = self.connection_model.routing_grid(
            input_ports, output_ports, input_channels, output_channels
        )

        # Keep rows for input channels that are gone for now, so the manual map survives
        self.map_rows = max(len(input_channels), len(input_device.get_selected_channel_list()))
        self.rendered_positions = [position for position, _unused in rows]

        if not rows or not cols:
            self.show_message(_('No ports available'))
            return

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(COLUMN_SPACING)

        # Column 0 and row 0 hold the axis markers, so the port names sit at column 1 and row 1
        # Checkboxes start at (2, 2)
        grid.attach(axis_marker(_('out')), 2, 0, len(cols), 1)
        grid.attach(axis_marker(_('in')), 0, 2, 1, len(rows))

        # Output port labels
        for column, (_unused, output_name) in enumerate(cols):
            label = Gtk.Label(label=port_label(output_name), halign=Gtk.Align.CENTER)
            grid.attach(label, column + 2, 1, 1, 1)

        # Input port labels + checkboxes
        for row, (position, input_name) in enumerate(rows):
            label = Gtk.Label(label=port_label(input_name))
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 1, row + 2, 1, 1)

            for column, (output_channel, _unused) in enumerate(cols):
                check = Gtk.CheckButton(active=(position, output_channel) in checked)
                check.set_sensitive(not self.connection_model.auto_ports)

                grid.attach(check, column + 2, row + 2, 1, 1)
                self.checkboxes[(position, output_channel)] = check
                check.connect('toggled', self._on_check_toggled)

        self.append(grid)

    def _on_check_toggled(self, _check):
        self.emit('changed')

    def show_message(self, text: str):
        self.append(Gtk.Label(label=text, halign=Gtk.Align.CENTER))

    def show_unavailable(self):
        self.show_message(_('Could not read device ports'))
