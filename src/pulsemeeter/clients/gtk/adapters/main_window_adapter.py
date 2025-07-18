from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget
from pulsemeeter.clients.gtk.widgets.app.app_box_widget import AppBoxWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class MainWindowAdapter(GObject.GObject):

    settings_button: Gtk.Button
    settings_widget: GObject
    device_grid: Gtk.Grid
    device_box: dict[str, dict[DeviceBoxWidget]]
    app_box: dict[str, AppBoxWidget]

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self):
        super().__init__()
        self.set_title("Pulsemeeter")
        for device_type in ('hi', 'vi', 'a', 'b'):
            self.device_box[device_type].connect('create_pressed', self.create_pressed)
            # self.device_box[device_type].connect('remove_pressed', self.remove_pressed)
            self.device_box[device_type].connect('add_device_pressed', self.add_device_pressed)

        self.settings_widget.connect('settings_change', self.save_settings)

    def save_settings(self, _, config_schema):
        self.emit('settings_change', config_schema)

    def add_device_pressed(self, _, device_type):
        self.emit('add_device_pressed', device_type)

    # def remove_pressed(self, _, device_type, device_id):
        # self.emit('device_remove', device_type, device_id)

    def create_pressed(self, _, device_schema):
        self.emit('device_new', device_schema)

    def _framed(self, widget, label):
        '''
        Returns a framed widget with the requested label
            "widget" is the widget that is going to be framed
            "label" is the label of the frame
        '''
        frame = Gtk.Frame(margin=5)
        title = Gtk.Label(label=label, margin=10)
        frame.set_label_widget(title)
        frame.set_label_align(0.5, 0)
        frame.add(widget)
        return frame
