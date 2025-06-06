import gettext

from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget
from pulsemeeter.clients.gtk.widgets.app.app_box_widget import AppBoxWidget
from pulsemeeter.clients.gtk.adapters.main_window_adapter import MainWindowAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class MainWindow(Gtk.Window, MainWindowAdapter):

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "device_remove": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, application, config_model, app_manager):
        Gtk.Window.__init__(self, application=application)
        self.device_grid = Gtk.Grid()
        self.config_model = config_model

        self.device_box = {}
        for device_type in ('hi', 'vi', 'a', 'b'):
            devices = config_model.device_manager.__dict__[device_type]
            self.device_box[device_type] = DeviceBoxWidget(devices, device_type, self.config_model.device_manager)

        sink_input_box = AppBoxWidget('sink_input', app_manager)
        source_output_box = AppBoxWidget('source_output', app_manager)

        self.device_grid.attach(self.device_box['hi'], 0, 0, 1, 1)
        self.device_grid.attach(self.device_box['vi'], 1, 0, 1, 1)
        self.device_grid.attach(self.device_box['a'], 0, 1, 1, 1)
        self.device_grid.attach(self.device_box['b'], 1, 1, 1, 1)
        self.device_grid.attach(sink_input_box, 0, 2, 1, 1)
        self.device_grid.attach(source_output_box, 1, 2, 1, 1)
        # self.device_grid.attach(self._framed(sink_input_box, 'Application Outputs'), 0, 2, 1, 1)
        # self.device_grid.attach(self._framed(source_output_box, 'Application Inputs'), 1, 2, 1, 1)

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        self.add(self.device_grid)

        self.devices = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.apps = {'sink_input': {}, 'source_output': {}}
        MainWindowAdapter.__init__(self, config_model=config_model, app_manager=app_manager)
        # self.load_apps()
