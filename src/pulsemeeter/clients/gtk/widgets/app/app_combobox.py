import gettext

# from pulsemeeter.clients.gtk.adapters.app_combobox_adapter import AppComboboxAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class AppCombobox(Gtk.ComboBox):

    _device_list = {
        'sink_input': Gtk.ListStore(str, str),
        'source_output': Gtk.ListStore(str, str)
    }

    def __init__(self, app_type: str):
        self.app_type = app_type
        device_list = self._device_list[app_type]
        super().__init__(
            model=device_list,
        )

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(0.5, 0.5)
        renderer.set_padding(6, 6)

        self.pack_start(renderer, True)
        self.add_attribute(renderer, "text", 0)

        accesible_description = _('Select the app %s! device') % app_type.split("_")[1] 
        self.set_tooltip_text(accesible_description)
        Gtk.Accessible.update_property(
            self,
            [
                Gtk.AccessibleProperty.DESCRIPTION,
            ],
            [
                accesible_description,
            ]
        )

    def set_active_device(self, device):
        device_list = self._device_list[self.app_type]

        count: int = 0
        for device_name in device_list:
            if device_name[0] == device:
                # print(device_name[0], device)
                self.set_active(count)
                return
            count += 1

            self.set_active(-1)

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

    def get_active_text(self):
        active_iter = self.get_active_iter()
        if active_iter is not None:
            return self._device_list[self.app_type].get_value(active_iter, 1)

        return None
