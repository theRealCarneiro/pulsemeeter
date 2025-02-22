# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DefaultWidget(Gtk.ToggleButton):

    def __init__(self, state: bool):
        icon = Gio.ThemedIcon(name='emblem-default-symbolic')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        super().__init__(
            hexpand=False,
            vexpand=False,
            valign=Gtk.Align.CENTER,
            image=image
        )

        if state is None:
            state = False
            self.set_visible(False)
            # self.no_show_all(True)

        self.set_active(state)
        if state is True:
            self.set_sensitive(False)

    def set_primary(self, state):
        self.set_active(state)
        self.set_sensitive(not state)
