from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema
from meexer.schemas.app_schema import AppSchema
from meexer.clients.gtk.widgets.device.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
from meexer.clients.gtk.widgets.common.icon_button_widget import IconButton

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceBox(Gtk.Frame):

    def __init__(self, label):
        super().__init__(margin=5)
        title = Gtk.Label(label, margin=10)

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

    def add_device(self, device):
        self.device_box.pack_start(device, False, False, 0)

    def remove_device(self, device):
        self.remove(device)


class MainWindow(Gtk.Window):

    def __init__(self, application):
        super().__init__(application=application)
        self.device_grid = Gtk.Grid()

        hi_box = DeviceBox('Hardware Inputs')
        vi_box = DeviceBox('Virtual Inputs')
        a_box = DeviceBox('Hardware Outputs')
        b_box = DeviceBox('Virtual Outputs')
        sink_input_box = Gtk.VBox()
        source_output_box = Gtk.VBox()

        self.device_grid.attach(hi_box, 0, 0, 1, 1)
        self.device_grid.attach(vi_box, 1, 0, 1, 1)
        self.device_grid.attach(a_box, 0, 1, 1, 1)
        self.device_grid.attach(b_box, 1, 1, 1, 1)
        self.device_grid.attach(self._framed(sink_input_box, 'Application Outputs'), 0, 2, 1, 1)
        self.device_grid.attach(self._framed(source_output_box, 'Application Inputs'), 1, 2, 1, 1)

        self.device_box = {'vi': vi_box, 'hi': hi_box, 'a': a_box, 'b': b_box}

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        self.add(self.device_grid)

        self.devices = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.apps = {'sink_input': [], 'source_output': []}

    def update_connection_buttons(self, device_type, device_id):
        device = self.devices[device_type][device_id]

        # new output added
        if device_type in ('a', 'b'):
            for input_type, input_id in self.iter_input():
                input_device = self.devices[input_type][input_id]
                connection_schema = ConnectionSchema(nick=device.get_nick())
                button = input_device.insert_connection_widget(device_type, device_id, connection_schema)
                yield button, input_type, input_id

        # When a new input is added, we gotta create the buttons to existing outputs
        else:
            for output_type, output_id in self.iter_output():
                output_device = self.devices[output_type][output_id]
                connection_schema = ConnectionSchema(nick=output_device.get_nick())
                button = device.insert_connection_widget(output_type, output_id, connection_schema)
                yield button, output_type, output_id

    def load_devices(self, devices_schema):
        for device_type in ('a', 'b', 'vi', 'hi'):
            for device_id, device_schema in devices_schema.__dict__[device_type].items():
                device = self.insert_device(device_type, device_id, device_schema)
                yield device_type, device_id, device

    def insert_device(self, device_type: str, device_id: str, device_schema: DeviceSchema):
        '''
        Insert a device widget and add it to a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to insert in the box
        '''
        device = DeviceWidget(device_schema, device_id)
        self.device_box[device_type].add_device(device)
        self.devices[device_type][device_id] = device
        return device

    def remove_device(self, device_type: str, device_id: str):
        '''
        Destroy a device widget and remove it from a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to remove from the box
        '''
        device = self.devices[device_type][device_id].pop()
        self.device_box[device_type].remove_device(device)

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
