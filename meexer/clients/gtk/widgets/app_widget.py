import logging

from meexer.schemas.app_schema import AppSchema
from meexer.clients.gtk.widgets.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.vumeter_widget import VumeterWidget
from meexer.clients.gtk.widgets.mute_widget import MuteWidget

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402


LOG = logging.getLogger("generic")


class AppWidget(Gtk.Frame):

    def __init__(self, app_schema: AppSchema):
        self.app_schema = app_schema
        super().__init__(margin=10)
        main_grid = Gtk.Grid(margin=5, hexpand=True)
        info_grid = Gtk.Grid(margin_start=8, hexpand=True)
        control_grid = Gtk.Grid(hexpand=True)
        self.add(main_grid)

        self.index = app_schema.index
        self.app_type = app_schema.app_type
        self.label = Gtk.Label(label=app_schema.label, margin_left=10, halign=Gtk.Align.START)
        self.icon = AppIcon(app_schema.icon)
        self.volume = VolumeWidget(app_schema.volume)
        self.combobox = AppCombobox(app_schema.device, app_schema.app_type)
        self.mute = MuteWidget(app_schema.mute)
        self.vumeter = VumeterWidget()

        main_grid.attach(info_grid, 0, 0, 1, 1)
        main_grid.attach(control_grid, 0, 1, 1, 1)

        info_grid.attach(self.icon, 0, 0, 1, 1)
        info_grid.attach(self.label, 1, 0, 1, 1)
        info_grid.attach(self.combobox, 2, 0, 1, 1)

        control_grid.attach(self.volume, 0, 0, 1, 1)
        control_grid.attach(self.mute, 1, 0, 1, 1)
        control_grid.attach(self.vumeter, 0, 1, 2, 1)


class AppIcon(Gtk.Image):

    def __init__(self, icon_name: str):
        icon = Gio.ThemedIcon(name=icon_name)
        super().__init__(margin_left=10, halign=Gtk.Align.START)
        super().set_from_gicon(icon, Gtk.IconSize.MENU)


class AppCombobox(Gtk.ComboBox):

    _device_list = {
        'sink_input': Gtk.ListStore(str),
        'source_output': Gtk.ListStore(str)
    }

    def __init__(self, device: str, app_type: str):
        print(device)
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
        return cls.device_list[app_type]
