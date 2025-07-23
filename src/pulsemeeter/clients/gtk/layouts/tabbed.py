import gettext

from pulsemeeter.clients.gtk.widgets.app.app_box_widget import AppBoxWidget
from pulsemeeter.clients.gtk.adapters.main_window_adapter import MainWindowAdapter
from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget
from pulsemeeter.clients.gtk.widgets.common.settings_menu_box import SettingsMenuBox

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


DEVICE_TYPE_PRETTY = {
    'hi': _('Hardware Inputs'),
    'vi': _('Virtual Inputs'),
    'a': _('Hardware Outputs'),
    'b': _('Virtual Outputs')
}


class MainWindow(Gtk.Window, MainWindowAdapter):

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT, str, str)),
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, application, config_model):
        Gtk.Window.__init__(self, application=application)

        notebook = Gtk.Notebook()
        self.settings_widget = SettingsMenuBox(config_model)

        # Create a tab for each device box.
        self.device_box = {}
        for device_type in ('hi', 'vi', 'a', 'b'):
            self.device_box[device_type] = DeviceBoxWidget(device_type)
            tab_label = Gtk.Label(label=DEVICE_TYPE_PRETTY[device_type])
            notebook.append_page(self.device_box[device_type], tab_label)

        sink_input_box = AppBoxWidget('sink_input')
        source_output_box = AppBoxWidget('source_output')
        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        notebook.append_page(sink_input_box, Gtk.Label(label=_("Application Outputs")))
        notebook.append_page(source_output_box, Gtk.Label(label=_("Application Inputs")))
        notebook.append_page(self.settings_widget, Gtk.Label('Settings'))

        self.add(notebook)
        MainWindowAdapter.__init__(self)
