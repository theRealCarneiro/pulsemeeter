import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DefaultWidget(Gtk.ToggleButton):

    __gsignals__ = {
        'primary': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, active: bool, *args, **kwargs):
        icon = Gio.ThemedIcon(name='emblem-default-symbolic')
        image = Gtk.Image.new_from_gicon(icon)
        super().__init__(active=active, *args, **kwargs)

        self.set_child(image)
        self._signal_handler_id = self.connect('toggled', self._on_toggled)
        Gtk.Accessible.update_property(self, [Gtk.AccessibleProperty.LABEL], [_('Primary')])
        self._update_tooltip(active)

    def _on_toggled(self, widget):
        if widget.get_active():
            self.emit('primary')

    def _update_tooltip(self, state):
        if state:
            self.set_tooltip_text(_('This device is primary'))
        else:
            self.set_tooltip_text(_('Set as primary device'))

    def set_primary(self, state):
        self.handler_block(self._signal_handler_id)
        self.set_active(state)
        self.handler_unblock(self._signal_handler_id)

    def get_primary(self):
        self.get_active()
