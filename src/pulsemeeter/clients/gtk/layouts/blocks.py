import gettext

from pulsemeeter.clients.gtk.widgets.app.app_box_widget import AppBoxWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.adapters.main_window_adapter import MainWindowAdapter
from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget
# from pulsemeeter.clients.gtk.widgets.common.settings_popover import SettingsMenuPopover
from pulsemeeter.clients.gtk.widgets.common.settings_menu_box import SettingsMenuBox

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class MainWindow(Gtk.Window, MainWindowAdapter):

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, application, config_model):
        Gtk.Window.__init__(self, application=application)
        self.device_grid = Gtk.Grid()

        self.settings_widget = SettingsMenuBox(config_model)
        self.settings_button = IconButton('open-menu-symbolic')

        self.settings_popover = Gtk.Popover(margin=10)
        self.settings_popover.set_modal(False)
        self.settings_popover.add(self.settings_widget)
        self.settings_popover.set_relative_to(self.settings_button)

        self.device_box = {}
        for device_type in ('hi', 'vi', 'a', 'b'):
            self.device_box[device_type] = DeviceBoxWidget(device_type)

        sink_input_box = AppBoxWidget('sink_input')
        source_output_box = AppBoxWidget('source_output')

        self.device_grid.attach(self.device_box['hi'], 0, 0, 1, 1)
        self.device_grid.attach(self.device_box['vi'], 1, 0, 1, 1)
        self.device_grid.attach(self.device_box['a'], 0, 1, 1, 1)
        self.device_grid.attach(self.device_box['b'], 1, 1, 1, 1)
        self.device_grid.attach(sink_input_box, 0, 2, 1, 1)
        self.device_grid.attach(source_output_box, 1, 2, 1, 1)

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        settings_box = Gtk.HBox(halign=Gtk.Align.END, valign=Gtk.Align.START, vexpand=False)
        settings_box.pack_start(self.settings_button, False, False, 5)

        mainbox = Gtk.VBox()
        mainbox.pack_start(settings_box, False, False, 5)
        mainbox.add(self.device_grid)
        self.add(mainbox)

        MainWindowAdapter.__init__(self)
        self.settings_button.connect('clicked', self.open_settings)

    def open_settings(self, _):
        self.settings_popover.popup()
        self.settings_popover.show_all()
