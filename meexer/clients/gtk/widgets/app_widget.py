from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import logging

from meexer.schemas.app_schema import AppSchema

from meexer.interface.widgets.volume_widget import VolumeWidget
from meexer.interface.widgets.vumeter_widget import VumeterWidget
from meexer.interface.widgets.mute_widget import MuteWidget


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
        self.combobox = AppCombobox(app_schema.device)
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

    device_list: Gtk.ListStore = Gtk.ListStore(str)

    def __init__(self, device: str):
        device_list = self.device_list
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
            if device_name == device[0]:
                self.set_active(count)
                break
            count += 1

    def get_active_text(self):
        active_iter = self.get_active_iter()
        if active_iter is not None:
            return self.device_list.get_value(active_iter, 0)

    @classmethod
    def set_device_list(cls, device_list):
        cls.device_list.clear()
        for device in device_list:
            cls.device_list.append([device])

    @classmethod
    def get_device_list(cls):
        return cls.device_list


# window = Gtk.Window()
# frame = Gtk.Frame(margin=5)
# frame.add(App())
# window.add(frame)
# window.show_all()
# window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
# AppCombobox.set_device_list(['Main', 'Music', 'Comn'])
# Gtk.main()
