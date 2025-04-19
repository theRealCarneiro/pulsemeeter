from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget
from pulsemeeter.clients.gtk.adapters.main_window_adapter import MainWindowAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


DEVICE_TYPE_PRETTY = {
    'hi': 'Hardware Inputs',
    'vi': 'Virtual Inputs',
    'a': 'Hardware Outputs',
    'b': 'Virtual Outputs'
}


class MainWindow(Gtk.Window, MainWindowAdapter):

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "device_remove": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, application, config_model, app_manager):
        Gtk.Window.__init__(self, application=application)
        self.set_title("Tabbed Layout Example")
        # self.set_default_size(800, 600)

        # Create a Notebook to hold tabs.
        notebook = Gtk.Notebook()

        # Create a tab for each device box.
        self.device_box = {}
        for device_type in ('hi', 'vi', 'a', 'b'):
            devices = getattr(config_model.device_manager, device_type)
            self.device_box[device_type] = DeviceBoxWidget(devices, device_type)
            tab_label = Gtk.Label(label=DEVICE_TYPE_PRETTY[device_type])
            notebook.append_page(self.device_box[device_type], tab_label)

        sink_input_box = Gtk.VBox(spacing=6)
        source_output_box = Gtk.VBox(spacing=6)

        framed_sink = self._framed(sink_input_box, 'Application Outputs')
        framed_source = self._framed(source_output_box, 'Application Inputs')

        notebook.append_page(framed_sink, Gtk.Label(label="Application Outputs"))
        notebook.append_page(framed_source, Gtk.Label(label="Application Inputs"))

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}
        self.devices = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.apps = {'sink_input': {}, 'source_output': {}}

        self.add(notebook)
        MainWindowAdapter.__init__(self, config_model=config_model, app_manager=app_manager)
        # self.load_apps()
