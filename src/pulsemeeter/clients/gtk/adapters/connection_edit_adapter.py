from typing import Literal

from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class ConnectionSettingsAdapter(GObject.GObject):
    '''
    A widget for creating a new device
    '''

    confirm_button: IconButton
    cancel_button: IconButton

    def __init__(self):
        super().__init__()
        self.connect("key-press-event", self._on_key_press)

    def _on_key_press(self, widget, event):
        # 65307 is the keyval for Escape
        if event.keyval == Gdk.KEY_Escape:
            self.popdown()
            return True
        return False

    def close_pressed(self, _):
        self.popdown()
