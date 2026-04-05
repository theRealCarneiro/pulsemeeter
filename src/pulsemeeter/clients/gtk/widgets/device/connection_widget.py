import gettext

from pulsemeeter.clients.gtk.widgets.popovers.edit_connection_widget import ConnectionSettingsPopup

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionWidget(Gtk.Box):

    __gsignals__ = {
        'connection': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'route_volume': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'use_loopback': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'settings_pressed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, label: str, connection_model, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, *args, **kwargs)
        self.set_hexpand(True)
        self.connection_model = connection_model

        # Toggle button (existing connection toggle)
        self.toggle_button = Gtk.ToggleButton(label=label, active=connection_model.state)
        self.toggle_button.set_size_request(120, -1)
        self._toggle_handler_id = self.toggle_button.connect('toggled', self._on_toggled)

        # Right-click gesture for connection settings popup
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", self._on_pressed)
        self.popover = ConnectionSettingsPopup(connection_model)
        self.popover.set_parent(self.toggle_button)
        self.toggle_button.add_controller(gesture)

        # Checkbox for use_loopback opt-in
        self.loopback_check = Gtk.CheckButton(active=connection_model.use_loopback)
        self.loopback_check.set_tooltip_text(_('Enable per-route volume (uses pw-loopback)'))
        self._loopback_handler_id = self.loopback_check.connect('toggled', self._on_loopback_toggled)

        # Volume slider for route volume
        self.volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.volume_scale.set_range(0, 153)
        self.volume_scale.set_increments(1, 5)
        self.volume_scale.set_digits(0)
        self.volume_scale.set_value(connection_model.route_volume)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.set_size_request(150, 0)
        self.volume_scale.add_mark(100, Gtk.PositionType.TOP, '')
        self.volume_scale.set_tooltip_text(_('Route volume'))
        self._volume_handler_id = self.volume_scale.connect('value-changed', self._on_volume_changed)

        # Pack widgets
        self.append(self.toggle_button)
        self.append(self.loopback_check)
        self.append(self.volume_scale)

        # Initial visibility
        self._update_visibility()
        self.set_accessible()

    def set_accessible(self):
        description_label = _('Connect to %s, right click to open connection settings') % self.connection_model.nick
        self.toggle_button.set_tooltip_text(description_label)
        Gtk.Accessible.update_property(self.toggle_button, [Gtk.AccessibleProperty.DESCRIPTION], [description_label])
        Gtk.Accessible.update_property(self.toggle_button, [Gtk.AccessibleProperty.HAS_POPUP], [True])

    def _update_visibility(self):
        '''Update visibility of checkbox and slider based on connection state and loopback flag.'''
        is_connected = self.toggle_button.get_active()
        use_loopback = self.loopback_check.get_active()
        self.loopback_check.set_visible(is_connected)
        self.volume_scale.set_visible(is_connected and use_loopback)

    def _on_toggled(self, widget):
        self._update_visibility()
        self.emit('connection', widget.get_active())

    def _on_loopback_toggled(self, widget):
        self._update_visibility()
        self.emit('use_loopback', widget.get_active())

    def _on_volume_changed(self, widget):
        self.emit('route_volume', int(widget.get_value()))

    def _on_pressed(self, _, __, ___, ____):
        self.popover.popup()
        self.emit('settings_pressed')

    def set_connection(self, state):
        self.toggle_button.handler_block(self._toggle_handler_id)
        self.toggle_button.set_active(state)
        self._update_visibility()
        self.toggle_button.handler_unblock(self._toggle_handler_id)

    def get_connection(self):
        return self.toggle_button.get_active()

    def set_route_volume(self, value):
        self.volume_scale.handler_block(self._volume_handler_id)
        self.volume_scale.set_value(value)
        self.volume_scale.handler_unblock(self._volume_handler_id)

    def set_use_loopback(self, state):
        self.loopback_check.handler_block(self._loopback_handler_id)
        self.loopback_check.set_active(state)
        self._update_visibility()
        self.loopback_check.handler_unblock(self._loopback_handler_id)
