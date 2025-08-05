# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class IconWidget(Gtk.Image):

    def __init__(self, icon_name: str, *args, **kwargs):
        icon = Gio.ThemedIcon(name=icon_name)
        super().__init__(*args, **kwargs)
        super().set_from_gicon(icon)
