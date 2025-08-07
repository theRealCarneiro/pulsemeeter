import gettext

from pulsemeeter.clients.gtk.widgets.popovers.edit_connection_widget import ConnectionSettingsPopup

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionWidget(Gtk.ToggleButton):

    __gsignals__ = {
        'connection': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'settings_pressed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, label: str, connection_model, *args, **kwargs):
        super().__init__(label=label, active=connection_model.state, *args, **kwargs)
        self.connection_model = connection_model
        self._signal_handler_id = self.connect('toggled', self._on_toggled)
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", self._on_pressed)
        self.popover = ConnectionSettingsPopup(connection_model)
        self.popover.set_parent(self)
        self.add_controller(gesture)
        self.set_accessible()

    def set_accessible(self):
        description_label = _('Connect to %s, right click to open connection settings') % self.connection_model.nick
        self.set_tooltip_text(description_label)
        Gtk.Accessible.update_property(self, [Gtk.AccessibleProperty.DESCRIPTION], [description_label])
        Gtk.Accessible.update_property(self, [Gtk.AccessibleProperty.HAS_POPUP], [True])

    def _on_toggled(self, widget):
        self.emit('connection', widget.get_active())

    def _on_pressed(self, _, __, ___, ____):
        self.popover.popup()
        self.emit('settings_pressed')

    def set_connection(self, state):
        self.handler_block(self._signal_handler_id)
        self.set_active(state)
        self.handler_unblock(self._signal_handler_id)

    def get_connection(self):
        return self.get_active()
