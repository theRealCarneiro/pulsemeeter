import math
import gettext

from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.clients.gtk.widgets.device.port_map_widget import PortMap, COLUMN_SPACING

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext

STATUS_WIDTH_WITHOUT_GRID = 200


def status_width(grid_width, columns, column_width):
    '''
    Width of the note under the routing grid: twice the width of a stereo grid, growing
    with the square root past that so wide grids do not get a needlessly wide note
        "columns" and "column_width" give the grid's output columns, from which the
        width the same grid would have with two of them is worked out
    '''
    stereo_width = grid_width - (columns - 2) * column_width
    return max(grid_width, round(2 * math.sqrt(stereo_width * grid_width)))


class ConnectionSettingsPopup(Gtk.Popover):
    '''
    Port settings of a route. Every change applies right away through the
    settings_changed signal, which carries a copy of the connection model with
    the change in it.
    '''

    __gsignals__ = {
        'settings_changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self, connection_model: ConnectionModel = None):

        super().__init__()
        self.connection_model = connection_model

        # create widgets
        self.auto_ports_check = Gtk.CheckButton(label=_("Auto ports"), halign=Gtk.Align.CENTER)
        self.port_map_widget = PortMap(connection_model)
        self.port_map_widget.set_halign(Gtk.Align.CENTER)

        # Centered note under the grid: the route's icon, then what is wrong and what to do about it
        self.status_icon = Gtk.Image(halign=Gtk.Align.CENTER)
        self.status_label = Gtk.Label(wrap=True, max_width_chars=1, xalign=0.5, justify=Gtk.Justification.CENTER)
        self.status_label.add_css_class('dim-label')
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, visible=False,
                                  margin_top=8, margin_start=4, margin_end=4)
        self.status_box.append(self.status_icon)
        self.status_box.append(self.status_label)

        # connect events
        self._auto_handler_id = self.auto_ports_check.connect('toggled', self._on_auto_toggled)
        self.port_map_widget.connect('changed', self._on_port_map_changed)

        main_box = Gtk.Box(hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=2)
        main_box.append(self.auto_ports_check)
        main_box.append(Gtk.Separator())
        main_box.append(self.port_map_widget)
        main_box.append(self.status_box)

        self.set_child(main_box)

    def fill_settings(self):
        # showing the saved setting is not a change made by the user
        self.auto_ports_check.handler_block(self._auto_handler_id)
        self.auto_ports_check.set_active(self.connection_model.auto_ports)
        self.auto_ports_check.handler_unblock(self._auto_handler_id)
        self.refresh_status()

    def refresh_status(self):
        '''
        Explain the route's warning or info icon, and how to keep the routing as it is
        '''
        model = self.connection_model
        lines = [text for text in (model.error_text(), model.warning_text()) if text]

        if model.order_pairs:
            lines.append(_('No matching channel names, matched channels by order.'))

        # manual routing is the user's own choice, so it shows neither of these
        if model.auto_ports and (model.unrouted_ports or model.order_pairs):
            lines.append(_('Untick Auto ports to keep this routing as your own and hide this warning.'))

        self.status_box.set_visible(bool(lines))
        if not lines:
            return

        problem = model.error_text() or model.warning_text()
        self.status_icon.set_from_icon_name('dialog-warning' if problem else 'dialog-information')
        text = GLib.markup_escape_text('\n'.join(lines))
        self.status_label.set_markup(f'<small>{text}</small>')
        self.status_box.set_tooltip_text(model.order_text() or None)

        # the label wraps to this width, so the grid rather than the text decides how wide the popover gets
        self.status_box.set_size_request(self._status_width(), -1)

    def _status_width(self):
        checkboxes = self.port_map_widget.checkboxes
        if not checkboxes:
            return STATUS_WIDTH_WITHOUT_GRID

        grid_width = self.port_map_widget.measure(Gtk.Orientation.HORIZONTAL, -1)[1]
        column_width = next(iter(checkboxes.values())).measure(Gtk.Orientation.HORIZONTAL, -1)[1] + COLUMN_SPACING
        columns = len({output_channel for _position, output_channel in checkboxes})
        return status_width(grid_width, columns, column_width)

    def _on_auto_toggled(self, widget):
        model = self.connection_model.model_copy(deep=True)
        model.auto_ports = widget.get_active()

        # The first switch to manual starts from the ticks automatic mapping shows, later ones restore the saved map
        if not model.auto_ports and not model.port_map:

            # with no grid (devices without ports) there are no ticks to start from, so stay on Auto
            if not self.port_map_widget.checkboxes:
                self.fill_settings()
                return

            model.port_map = self.port_map_widget.get_port_map()

        self.emit('settings_changed', model)

    def _on_port_map_changed(self, _widget):
        model = self.connection_model.model_copy(deep=True)
        model.port_map = self.port_map_widget.get_port_map()
        self.emit('settings_changed', model)
