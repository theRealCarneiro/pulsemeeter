# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class MuteWidget(Gtk.ToggleButton):

    def __init__(self, state: bool):
        icon = Gio.ThemedIcon(name='audio-volume-muted')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        super().__init__(
            active=state,
            hexpand=False,
            vexpand=False,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.END,
            image=image
        )

        self.signal_handler = {}
