# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class IconWidget(Gtk.Image):

    def __init__(self, icon_name: str):
        icon = Gio.ThemedIcon(name=icon_name)
        super().__init__(margin_left=10, halign=Gtk.Align.START)
        super().set_from_gicon(icon, Gtk.IconSize.MENU)
