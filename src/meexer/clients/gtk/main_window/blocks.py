from meexer.clients.gtk.widgets.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app_widget import AppWidget
from meexer.clients.gtk.widgets.device_box import DeviceBox

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class MainWindow(Gtk.Window):

    def __init__(self, application):
        super().__init__(application=application)
        self.device_grid = Gtk.Grid()

        hi_box = DeviceBox('Hardware Inputs')
        vi_box = DeviceBox('Virtual Inputs')
        a_box = DeviceBox('Hardware Outputs')
        b_box = DeviceBox('Virtual Outputs')

        self.device_grid.attach(hi_box, 0, 0, 1, 1)
        self.device_grid.attach(vi_box, 1, 0, 1, 1)
        self.device_grid.attach(a_box, 0, 1, 1, 1)
        self.device_grid.attach(b_box, 1, 1, 1, 1)

        sink_input_box = Gtk.VBox()
        source_output_box = Gtk.VBox()
        self.device_grid.attach(self._framed(sink_input_box, 'Application Outputs'), 0, 2, 1, 1)
        self.device_grid.attach(self._framed(source_output_box, 'Application Inputs'), 1, 2, 1, 1)

        self.device_box = {'vi': vi_box, 'hi': hi_box, 'a': a_box, 'b': b_box}

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        self.add(self.device_grid)

    def insert_device(self, device_type: str, device: DeviceWidget):
        '''
        Insert a device widget and add it to a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to insert in the box
        '''
        self.device_box[device_type].add_device(device)

    def remove_device(self, device_type: str, device: DeviceWidget):
        '''
        Destroy a device widget and remove it from a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to remove from the box
        '''
        self.device_box[device_type].remove_device(device)

    def insert_app(self, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_widget.app_type].pack_start(app_widget, False, False, 0)

    def remove_app(self, app_widget: AppWidget):
        '''
        Insert an app widget to a device box
            "app_widget" is the app widget to remove from the box
        '''
        self.app_box[app_widget.app_type].remove(app_widget)

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
