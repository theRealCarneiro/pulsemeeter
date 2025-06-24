import gettext
import logging

from pulsemeeter.model.app_model import AppModel
from pulsemeeter.schemas.typing import AppType
from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget
from pulsemeeter.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from pulsemeeter.clients.gtk.widgets.common.mute_widget import MuteWidget
from pulsemeeter.clients.gtk.widgets.common.icon_widget import IconWidget
from pulsemeeter.clients.gtk.widgets.app.app_combobox import AppCombobox
from pulsemeeter.clients.gtk.adapters.app_adapter import AppAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


LOG = logging.getLogger("generic")


class AppWidget(Gtk.Frame, AppAdapter):

    __gsignals__ = {
        "app_mute": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "app_volume": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        "app_device_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, app_model: AppModel):
        self.app_model = app_model
        Gtk.Frame.__init__(self, margin=10)

        self.get_accessible().set_name(app_model.label)

        main_grid = Gtk.Grid(margin=5, hexpand=True)
        info_grid = Gtk.Grid(margin_start=8, hexpand=True)
        control_grid = Gtk.Grid(hexpand=True)
        self.add(main_grid)

        # self.from_model(app_model)
        self.app_type = app_model.app_type
        self.label = Gtk.Label(label=app_model.label, margin_left=10, halign=Gtk.Align.START)
        self.icon = IconWidget(app_model.icon)
        self.volume_widget = VolumeWidget(app_model.volume)
        self.combobox = AppCombobox(app_model.app_type)
        self.mute_widget = MuteWidget(app_model.mute)
        self.vumeter = VumeterWidget()
        self.handlers = {}

        GLib.idle_add(self.combobox.set_active_device, app_model.device)

        main_grid.attach(info_grid, 0, 0, 1, 1)
        main_grid.attach(control_grid, 0, 1, 1, 1)

        info_grid.attach(self.icon, 0, 0, 1, 1)
        info_grid.attach(self.label, 1, 0, 1, 1)
        info_grid.attach(self.combobox, 2, 0, 1, 1)

        control_grid.attach(self.volume_widget, 0, 0, 1, 1)
        control_grid.attach(self.mute_widget, 1, 0, 1, 1)
        control_grid.attach(self.vumeter, 0, 1, 2, 1)

        self.volume_widget.get_accessible().set_name(_("Volume"))
        self.mute_widget.get_accessible().set_name(_("Mute"))
        self.combobox.get_accessible().set_name(_("Select Device"))
        self.combobox.set_tooltip_text(_('Select the app %s! device') % self.app_type.split("_")[1])

        AppAdapter.__init__(self)
