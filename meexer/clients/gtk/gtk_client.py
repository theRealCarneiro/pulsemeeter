from meexer.ipc.client import Client
from meexer.clients.gtk.main_window import blocks
from meexer.schemas.config_schema import ConfigSchema
from meexer.schemas.device_schema import DeviceSchema
from meexer.schemas.app_schema import AppSchema
from meexer.model.app_model import AppModel

from meexer.clients.gtk.widgets.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app_widget import AppWidget, AppCombobox
from meexer.clients.gtk.services import app_service, device_service

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


class GtkClient(Gtk.Application):

    def __init__(self):
        super().__init__(application_id='org.pulsemeeter.meexer')
        self.window = None
        self.client = Client(listen_flags=0, instance_name='gtk')
        res = self.client.send_request('get_config', {})
        self.config = ConfigSchema(**res.data)
        self.devices = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.device_handlers = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.apps = {'sink_input': {}, 'source_output': {}}
        self.app_handlers = {'sink_input': {}, 'source_output': {}}

    def create_window(self):
        window = blocks.MainWindow(application=self)

        # load devices
        for device_type in ('a', 'b', 'vi', 'hi'):
            for device_id, device_schema in self.config.__dict__[device_type].items():
                device = self.create_device(device_type, device_id, device_schema)
                window.insert_device(device_type, device)

        sink_input_device_list = [
            device.name for device_id, device in self.config.__dict__['vi'].items()
        ]

        source_output_device_list = [
            device.name for device_id, device in self.config.__dict__['b'].items()
        ]

        source_output_device_list += sink_input_device_list

        AppCombobox.set_device_list('sink_input', sink_input_device_list)
        AppCombobox.set_device_list('source_output', source_output_device_list)

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
        self.device_handlers[device_type][device_id] = {}
        device_handle = self.device_handlers[device_type][device_id]

        # TODO: connect vumeters

        # connect mute signal
        device_handle['mute'] = device.mute.connect(
            'toggled', device_service.mute, device_type, device_id
        )

        # connect volume change signal
        device_handle['volume'] = device.volume.connect(
            'value-changed', device_service.volume, device_type, device_id
        )

        # connect default signal
        device_handle['default'] = device.default.connect(
            'toggled', device_service.default, device_type, device_id
        )

        # connect change last default device state
        device_handle['default_after'] = device.default.connect_after(
            'toggled', self.change_default_state, device_type, device_id
        )

        # interate connection buttons
        for output_type, buttons in device.connection_buttons.items():
            device_handle[output_type] = {}
            for output_id, button in buttons.items():

                # connect connection signals
                device_handle[output_type][output_id] = button.connect(
                    'toggled', device_service.connect, device_type, device_id,
                    output_type, output_id
                )

        self.devices[device_type][device_id] = device

        return device

    def remove_device(self, device_type: str, device_id: str):
        device = self.devices[device_type].pop(device_id)
        self.device_handlers[device_type].pop(device_id)
        self.window.remove_device(device_type, device)
        device.destroy()

    def create_app(self, app_schema: AppSchema):
        '''
        Create an app widget and add it to an app box
        '''
        app = AppWidget(app_schema)
        self.app_handlers[app_schema.app_type][app_schema.index] = {}
        app_handler = self.app_handlers[app_schema.app_type][app_schema.index]

        app_handler['volume'] = app.volume.connect(
            'value-changed', app_service.volume, app_schema.app_type, app_schema.index
        )
        app_handler['mute'] = app.mute.connect(
            'toggled', app_service.mute, app_schema.app_type, app_schema.index
        )
        app_handler['combobox'] = app.combobox.connect(
            'changed', app_service.move, app_schema.app_type, app_schema.index
        )
        # TODO: connect vumeter

        self.apps[app.app_type][app.index] = app

        return app

    def remove_app(self, app_schema: AppSchema):
        '''
        Delete an app widget
        '''
        app = self.apps[app_schema.app_type].pop(app_schema.index)
        self.app_handlers[app_schema.app_type].pop(app_schema.index)
        self.window.remove_app(app)
        app.destroy()

    def change_default_state(self, widget, device_type: str, device_id: str):
        '''
        Called after a default request has been sent, removes the previous default
        device as default
        '''

        # disable widget
        widget.set_sensitive(False)

        # search device handler
        for target_id, device in self.devices[device_type].items():
            if device_id != target_id and device.default.get_active():

                # get handlers
                device_handlers = self.device_handlers[device_type][target_id]
                handler = device_handlers['default']
                handler_after = device_handlers['default_after']

                # block signal handler
                device.default.handler_block(handler)
                device.default.handler_block(handler_after)

                # reset state and sensitivity
                device.default.set_active(False)
                device.default.set_sensitive(True)

                # unblock signal handler
                device.default.handler_unblock(handler)
                device.default.handler_unblock(handler_after)

                break

    def on_quit(self):
        self.quit()
