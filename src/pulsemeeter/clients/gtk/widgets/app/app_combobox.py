from pulsemeeter.clients.gtk.adapters.app_combobox_adapter import AppComboboxAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class AppCombobox(Gtk.ComboBox, AppComboboxAdapter):

    def __init__(self, app_type: str):
        self.app_type = app_type
        device_list = self._device_list[app_type]
        super().__init__(
            model=device_list,
            hexpand=True,
            margin_right=10,
            halign=Gtk.Align.END
        )

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(0.5, 0.5)
        renderer.set_padding(6, 6)

        self.pack_start(renderer, True)
        self.add_attribute(renderer, "text", 0)

    def get_active_text(self):
        active_iter = self.get_active_iter()
        if active_iter is not None:
            return self._device_list[self.app_type].get_value(active_iter, 0)

        return None

    def set_active_device(self, device):
        device_list = self._device_list[self.app_type]

        count: int = 0
        for device_name in device_list:
            if device_name[0] == device:
                print(device_name[0], device)
                self.set_active(count)
                break
            count += 1
