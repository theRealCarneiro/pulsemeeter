# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class AppComboboxAdapter(GObject.GObject):

    _device_list = {
        'sink_input': Gtk.ListStore(str, str),
        'source_output': Gtk.ListStore(str, str)
    }

    @classmethod
    def set_device_list(cls, app_type, device_list):
        cls._device_list[app_type].clear()
        # cls._device_list[app_type].append([])
        for device in device_list:
            cls._device_list[app_type].append(device)

    @classmethod
    def append_device_list(cls, app_type, device):
        cls._device_list[app_type].append(device)

    @classmethod
    def remove_device_list(cls, app_type, device):
        for row in cls._device_list[app_type]:
            if device[0] == row[0]:
                cls._device_list[app_type].remove(row.iter)

    @classmethod
    def get_device_list(cls, app_type):
        return cls._device_list[app_type]
