import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class MuteWidget(Gtk.ToggleButton):

    __gsignals__ = {
        'mute': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
    }

    def __init__(self, active: bool, *args, **kwargs):
        icon = Gio.ThemedIcon(name='audio-volume-muted')
        image = Gtk.Image.new_from_gicon(icon)
        super().__init__(active=active, *args, **kwargs)
        self.set_child(image)
        self._signal_handler_id = self.connect('toggled', self._on_toggled)
        Gtk.Accessible.update_property(self, [Gtk.AccessibleProperty.LABEL], [_('Mute')])
        self.set_tooltip_text(_('Mute toggle'))

    def _on_toggled(self, widget):
        self.emit('mute', widget.get_active())

    def set_mute(self, state):
        self.handler_block(self._signal_handler_id)
        self.set_active(state)
        self.handler_unblock(self._signal_handler_id)

    def get_mute(self):
        return self.get_active()
