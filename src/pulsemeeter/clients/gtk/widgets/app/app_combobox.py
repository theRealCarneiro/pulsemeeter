# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class AppCombobox(Gtk.ComboBox):

    _device_list = {
        'sink_input': Gtk.ListStore(str),
        'source_output': Gtk.ListStore(str)
    }

    def __init__(self, device: str, app_type: str):
        # print(device)
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

        count: int = 0
        for device_name in device_list:
            if device_name[0] == device:
                self.set_active(count)
                break
            count += 1

    def get_active_text(self, app_type):
        active_iter = self.get_active_iter()
        if active_iter is not None:
            return self._device_list[app_type].get_value(active_iter, 0)

        return None

    @classmethod
    def set_device_list(cls, app_type, device_list):
        cls._device_list[app_type].clear()
        for device in device_list:
            cls._device_list[app_type].append([device])

    @classmethod
    def append_device_list(cls, app_type, device):
        cls._device_list[app_type].append([device])

    @classmethod
    def remove_device_list(cls, app_type, device):
        for row in cls._device_list[app_type]:
            if device == row[0]:
                cls._device_list[app_type].remove(row.iter)

    @classmethod
    def get_device_list(cls, app_type):
        return cls._device_list[app_type]

