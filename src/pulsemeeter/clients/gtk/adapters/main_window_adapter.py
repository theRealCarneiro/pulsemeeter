from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.schemas.app_schema import AppSchema
from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
from pulsemeeter.clients.gtk.widgets.device.device_box_widget import DeviceBoxWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class MainWindowAdapter(GObject.GObject):

    config_model: ConfigModel
    device_grid: Gtk.Grid
    device_box: dict[str, dict[DeviceBoxWidget]]
    app_box: dict[str, Gtk.Box]
    devices: dict[str, dict[str, DeviceWidget]] = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
    apps: dict[str, dict[int, AppWidget]] = {'sink_input': {}, 'source_output': {}}

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "device_remove": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, config_model, app_manager):
        super().__init__()
        self.set_title("Pulsemeeter")
        self.config_model = config_model
        self.app_manager = app_manager
        for device_type in ('hi', 'vi', 'a', 'b'):
            self.device_box[device_type].connect('create_pressed', self.create_pressed)
            self.device_box[device_type].connect('remove_pressed', self.remove_pressed)
            self.device_box[device_type].connect('add_device_pressed', self.add_device_pressed)

        # self.config_model.device_manager.connect('device_new', self.insert_device)
        # self.config_model.device_manager.connect('device_remove', self.remove_device)

    # def load_devices(self, devices_schema):
    #     for device_type in ('a', 'b', 'vi', 'hi'):
    #         for device_id, device_model in devices_schema.__dict__[device_type].items():
    #             device = self.insert_device(device_type, device_id, device_model)
    #             yield device_type, device_id, device

    def create_device(self, device_type, device_id, device_model):
        device = self.insert_device(device_type, device_id, device_model)
        self.refresh_devices()
        return device
        # self.config_model.device_manager.create_device(device_dict)

    def refresh_devices(self):
        for device_type in ['vi', 'hi']:
            for device_id, device in self.device_box[device_type].devices.items():
                device.connections_widget.refresh_connections()
                device.connections_widget.show_all()

    def insert_device(self, device_type: str, device_id: str, device_model: DeviceModel) -> DeviceWidget:
        '''
        Insert a device widget and add it to a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to insert in the box
        '''
        device_widget = self.device_box[device_type].insert_device(device_model, device_id)
        return device_widget

    def remove_device(self, device_type: str, device_id: str) -> DeviceWidget:
        '''
        Destroy a device widget and remove it from a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to remove from the box
        '''
        self.config_model.device_manager.remove_device(device_type, device_id)
        return self.device_box[device_type].remove_device(device_id)

    # def load_apps(self):
    #     for app_type in ('sink_input', 'source_output'):
    #         for app_index, app_model in self.app_manager.__dict__[app_type].items():
    #             app = AppWidget(app_model)
    #             self.insert_app(app_type, app_index, app)

    # def load_apps(self, app_list, sink_input_device_list, source_output_device_list):
    #     AppCombobox.set_device_list('sink_input', sink_input_device_list)
    #     AppCombobox.set_device_list('source_output', source_output_device_list)
    #
    #     # load apps
    #     for app_type in ('sink_input', 'source_output'):
    #         for schema in app_list[app_type]:
    #             app_schema = AppSchema(**schema)
    #             app = AppWidget(app_schema)
    #             self.insert_app(app)

    def insert_app(self, app_type, app_index, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_type].insert_app(app_widget, False, False, 0)
        self.apps[app_type][app_index] = app_widget

    def remove_app(self, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_widget.app_type].remove(app_widget)
        self.apps[app_widget.app_type].remove(app_widget)

    def set_volume(self, device_type, device_id, volume: int):
        device = self.device_box.devices[device_type][device_id]
        device.set_volume(volume, emit=False)

    def set_mute(self, device_type, device_id, state: bool):
        device = self.device_box.devices[device_type][device_id]
        device.set_mute(state, emit=False)

    def set_primary(self, device_type, device_id):
        device = self.device_box.devices[device_type][device_id]
        if device.primary is True:
            return

        for other_device_id, other_device in self.device_box.devices[device_type].items():
            if device_id != other_device_id:
                other_device.set_primary(False, emit=False)

        device.set_primary(True, emit=False)

    def set_connection(self, output_type, output_id, input_type, input_id, state: bool):
        device = self.device_box.devices[input_type][input_id]
        device.set_connection(output_type, output_id, state, emit=False)

    def add_device_pressed(self, _, device_type):
        self.emit('add_device_pressed', device_type)

    def remove_pressed(self, _, device_type, device_id):
        self.emit('device_remove', device_type, device_id)

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
