from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk

from meexer.ipc.client import Client
from meexer.clients.gtk.main_window import blocks
# from meexer.schemas.device_schema import DeviceSchema
from meexer.schemas.config_schema import ConfigSchema
from meexer.schemas.device_schema import DeviceSchema
from meexer.schemas.app_schema import AppSchema
from meexer.model.app_model import AppModel

from meexer.clients.gtk.widgets.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app_widget import AppWidget
from meexer.clients.gtk.services import app_service, device_service


class GtkClient(Gtk.Application):

    def __init__(self):
        super().__init__(application_id='org.pulsemeeter.meexer')
        self.window = None
        self.client = Client(listen_flags=0, instance_name='gtk')
        res = self.client.send_request('get_config', {})
        self.config = ConfigSchema(**res.data)
        self.devices = dict(a={}, b={}, vi={}, hi={})
        self.apps = dict(sink_input={}, source_output={})

    def create_window(self):
        window = blocks.MainWindow(application=self)

        # load devices
        for device_type in ('a', 'b', 'vi', 'hi'):
            for device_id, device_schema in self.config.__dict__[device_type].items():
                device = self.create_device(device_type, device_id, device_schema)
                window.insert_device(device_type, device)

        # load apps
        for app_type in ('sink_input', 'source_output'):
            for app_schema in AppModel.list_apps(app_type):
                app = self.create_app(app_schema)
                window.insert_app(app)

        return window

    def do_activate(self):

        # TODO: layouts
        if self.window is None:
            self.window = self.create_window()

        self.window.show_all()
        self.window.present()

    def create_device(self, device_type: str, device_id: str, device_schema: DeviceSchema):
        '''
        Create a device widget and add it to it's box
        '''

        device = DeviceWidget(device_schema)

        # TODO: connect vumeters

        # connect mute signal
        device.mute.connect('toggled', device_service.mute, device_type, device_id)

        # connect volume change signal
        device.volume.connect('value-changed', device_service.volume, device_type, device_id)

        # connect default signals
        if device.default is not None:
            device.default.connect('toggled', device_service.default, device_type, device_id)

        # connect connection signals
        for output_type, buttons in device.connection_buttons.items():
            for output_id, button in buttons:
                button.connect('toggled', device_service.connect, device_type, device_id,
                               output_type, output_id)

        self.devices[device_type][device_id] = device

        return device

    def remove_device(self, device_type: str, device_id: str):
        device = self.devices[device_type].pop(device_id)
        self.window.remove_device(device_type, device)
        device.destroy()

    def create_app(self, app_schema: AppSchema):
        '''
        Create an app widget and add it to an app box
        '''
        app = AppWidget(app_schema)

        # TODO: volume signal
        # TODO: mute signal
        # TODO: device change signal
        # TODO: vumeter signal

        self.apps[app.app_type][app.index] = app

        return app

    def remove_app(self, app_schema: AppSchema):
        '''
        Delete an app widget
        '''
        app = self.apps[app_schema.app_type].pop(app_schema.index)
        self.window.remove_app(app)
        app.destroy()

    def on_quit(self):
        self.quit()


# app = GtkClient()
# app.run()
