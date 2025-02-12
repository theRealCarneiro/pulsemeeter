import logging

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


LOG = logging.getLogger("generic")


class DeviceBox(Gtk.Frame):

    def __init__(self, label):
        super().__init__(margin=5)
        title = Gtk.Label(label, margin=10)

        icon = Gio.ThemedIcon(name='add')
        image = Gtk.Image()
        image.set_from_gicon(icon, Gtk.IconSize.MENU)
        button = Gtk.Button()
        button.add(image)

        title_box = Gtk.HBox()
        title_box.add(title)
        title_box.add(button)

        self.set_label_widget(title_box)
        self.set_label_align(0.5, 0)

        self.device_box = Gtk.VBox()

        self.title = title
        self.add_device_button = button

    def add_device(self, device):
        self.device_box.pack_start(device, False, False, 0)

    def remove_device(self, device):
        self.remove(device)
