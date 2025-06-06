# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class IconButton(Gtk.Button):
    '''
    A button with an icon
    '''

    def __init__(self, icon_name: str):
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image()
        image.set_from_gicon(icon, Gtk.IconSize.MENU)
        super().__init__()
        self.add(image)



