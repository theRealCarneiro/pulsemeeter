from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema
from meexer.schemas.app_schema import AppSchema
from meexer.clients.gtk.widgets.device.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
from meexer.clients.gtk.widgets.common.icon_button_widget import IconButton
from meexer.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceBox(Gtk.Frame):

    device_label = {
        'hi': 'Hardware Inputs',
        'vi': 'Virtual Inputs',
        'a': 'Hardware Outputs',
        'b': 'Virtual Outputs',
    }

    def __init__(self, devices_schema: DeviceSchema, device_type: str):
        super().__init__(margin=5)

        self.device_type = device_type
        self.devices: dict[str, DeviceWidget] = {}

        title = Gtk.Label(self.device_label[device_type], margin=10)

        button = IconButton('add')

        title_box = Gtk.HBox()
        title_box.add(title)
        title_box.add(button)

        self.set_label_widget(title_box)
        self.set_label_align(0.5, 0)

        self.device_box = Gtk.VBox()
        self.add(self.device_box)

        self.title = title
        self.add_device_button = button
        self.add_device_button.connect('pressed', self.create_new_device_popover)

        # get what popup should be used
        dc = 'hardware' if device_type in ('a', 'hi') else 'virtual'
        popup_type = HardwareDevicePopup if dc == 'hardware' else VirtualDevicePopup
        self.popover = popup_type(device_type)
        self.popover.set_relative_to(self.add_device_button)
        # self.popover.popdown()

        self.load_devices(devices_schema)

    def load_devices(self, devices_schema: dict[str, DeviceSchema]):
        for device_id, device_schema in devices_schema.items():
            self.insert_device(device_schema, device_id)

    def insert_device(self, device_schema: DeviceSchema, device_id: str) -> DeviceWidget:
        device = DeviceWidget(device_schema, device_id)
        self.device_box.pack_start(device, False, False, 0)
        self.devices[device_id] = device
        return device

    def remove_device(self, device_id: str) -> DeviceWidget:
        device_widget = self.devices.pop(device_id)
        self.remove(device_widget)
        device_widget.destroy()
        return device_widget

    def create_new_device_popover(self, _):
        '''
            Opens create device popover when clicking on the new device button
        '''

        # create popup
        self.popover.show_all()
        self.popover.popup()


class MainWindow(Gtk.Window):

    def __init__(self, application, config_schema):
        super().__init__(application=application)
        self.device_grid = Gtk.Grid()

        self.device_box = {}
        for device_type in ('hi', 'vi', 'a', 'b'):
            self.device_box[device_type] = DeviceBox(config_schema.__dict__[device_type], device_type)

        sink_input_box = Gtk.VBox()
        source_output_box = Gtk.VBox()

        self.device_grid.attach(self.device_box['hi'], 0, 0, 1, 1)
        self.device_grid.attach(self.device_box['vi'], 1, 0, 1, 1)
        self.device_grid.attach(self.device_box['a'], 0, 1, 1, 1)
        self.device_grid.attach(self.device_box['b'], 1, 1, 1, 1)
        self.device_grid.attach(self._framed(sink_input_box, 'Application Outputs'), 0, 2, 1, 1)
        self.device_grid.attach(self._framed(source_output_box, 'Application Inputs'), 1, 2, 1, 1)

        # self.device_box = {'vi': vi_box, 'hi': hi_box, 'a': a_box, 'b': b_box}

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        self.add(self.device_grid)

        self.devices = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.apps = {'sink_input': [], 'source_output': []}

    def load_devices(self, devices_schema):
        for device_type in ('a', 'b', 'vi', 'hi'):
            for device_id, device_schema in devices_schema.__dict__[device_type].items():
                device = self.insert_device(device_type, device_id, device_schema)
                yield device_type, device_id, device

    def insert_device(self, device_type: str, device_id: str, device_schema: DeviceSchema) -> DeviceWidget:
        '''
        Insert a device widget and add it to a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to insert in the box
        '''
        return self.device_box[device_type].insert_device(device_schema, device_id)

    def remove_device(self, device_type: str, device_id: str) -> DeviceWidget:
        '''
        Destroy a device widget and remove it from a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to remove from the box
        '''
        return self.device_box[device_type].remove_device(device_id)

    def load_apps(self, app_list, sink_input_device_list, source_output_device_list):
        AppCombobox.set_device_list('sink_input', sink_input_device_list)
        AppCombobox.set_device_list('source_output', source_output_device_list)

        # load apps
        for app_type in ('sink_input', 'source_output'):
            for schema in app_list[app_type]:
                app_schema = AppSchema(**schema)
                app = AppWidget(app_schema)
                self.insert_app(app)

    def insert_app(self, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_widget.app_type].pack_start(app_widget, False, False, 0)
        self.apps[app_widget.app_type].append(app_widget)

    def remove_app(self, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_widget.app_type].remove(app_widget)
        self.apps[app_widget.app_type].remove(app_widget)

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

    def iter_input(self):
        for device_type in ('hi', 'vi'):
            for device_id in self.devices[device_type]:
                yield device_type, device_id

    def iter_output(self):
        for device_type in ('a', 'b'):
            for device_id in self.devices[device_type]:
                yield device_type, device_id

    def iter_hardware(self):
        for device_type in ('hi', 'a'):
            for device_id in self.devices[device_type]:
                yield device_type, device_id

    def iter_virtual(self):
        for device_type in ('vi', 'b'):
            for device_id in self.devices[device_type]:
                yield device_type, device_id

    def iter_all(self):
        for device_type in ('vi', 'hi', 'a', 'b'):
            for device_id in self.devices[device_type]:
                yield device_type, device_id
