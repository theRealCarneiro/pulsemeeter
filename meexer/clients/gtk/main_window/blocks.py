import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from meexer.clients.gtk.widgets.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app_widget import AppWidget


class MainWindow(Gtk.Window):

    def __init__(self, application):
        super().__init__(application=application)
        self.device_grid = Gtk.Grid()

        vi_box = Gtk.VBox()
        hi_box = Gtk.VBox()
        a_box = Gtk.VBox()
        b_box = Gtk.VBox()

        sink_input_box = Gtk.VBox()
        source_output_box = Gtk.VBox()

        self.device_grid.attach(self._framed(hi_box, 'Hardware Inputs'), 0, 0, 1, 1)
        self.device_grid.attach(self._framed(vi_box, 'Virtual Inputs'), 1, 0, 1, 1)
        self.device_grid.attach(self._framed(a_box, 'Hardware Outputs'), 0, 1, 1, 1)
        self.device_grid.attach(self._framed(b_box, 'Virtual Outputs'), 1, 1, 1, 1)
        self.device_grid.attach(self._framed(sink_input_box, 'Application Outputs'), 0, 2, 1, 1)
        self.device_grid.attach(self._framed(source_output_box, 'Application Inputs'), 1, 2, 1, 1)

        self.device_box = {'vi': vi_box, 'hi': hi_box, 'a': a_box, 'b': b_box}

        self.app_box = {'sink_input': sink_input_box, 'source_output': source_output_box}

        self.add(self.device_grid)

    def insert_device(self, device_type: str, device: DeviceWidget):
        '''
        Insert a device widget and add it to a device box
        '''
        self.device_box[device_type].pack_start(device, False, False, 0)

    def destroy_device(self, device_type: str, device: DeviceWidget):
        '''
        Destroy a device widget and remove it from a device box
        '''
        self.device_box[device_type].remove(device)

    def insert_app(self, app_widget: AppWidget):
        '''
        Create a device widget and add it to a device box
        '''
        self.app_box[app_widget.app_type].pack_start(app_widget, False, False, 0)

    def _framed(self, widget, label):
        '''
        Returns a framed widget with the requested label
        '''
        frame = Gtk.Frame(margin=5)
        frame.set_label_widget(Gtk.Label(label=label, margin=10))
        frame.set_label_align(0.5, 0)
        frame.add(widget)
        return frame
