import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class AppDropDown(Gtk.DropDown):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    _string_list = {
        'sink_input': Gtk.StringList(),
        'source_output': Gtk.StringList()
    }

    _device_data = {
        'sink_input': [],
        'source_output': []
    }

    def __init__(self, app_type: str):
        self.app_type = app_type
        super().__init__(
            model=self._string_list[app_type],
        )

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

        self.connect('notify::selected', self._on_selected)

    def _on_selected(self, widget, pspec):
        self.emit('changed')

    def set_active_device(self, device):
        device_data = self._device_data[self.app_type]

        for i, entry in enumerate(device_data):
            if entry[0] == device:
                self.set_selected(i)
                return

        self.set_selected(0)

    @classmethod
    def set_device_list(cls, app_type, device_list):
        cls._device_data[app_type] = list(device_list)
        nicks = [entry[0] for entry in device_list]
        string_list = cls._string_list[app_type]
        string_list.splice(0, string_list.get_n_items(), nicks)

    @classmethod
    def append_device_list(cls, app_type, device):
        cls._device_data[app_type].append(list(device))
        cls._string_list[app_type].append(device[0])

    @classmethod
    def remove_device_list(cls, app_type, device):
        data = cls._device_data[app_type]
        for i, entry in enumerate(data):
            if device[0] == entry[0]:
                data.pop(i)
                cls._string_list[app_type].remove(i)
                return

    @classmethod
    def get_device_list(cls, app_type):
        return cls._device_data[app_type]

    def get_active_text(self):
        index = self.get_selected()
        if index == Gtk.INVALID_LIST_POSITION:
            return None
        data = self._device_data[self.app_type]
        if index < len(data):
            return data[index][1]
        return None
