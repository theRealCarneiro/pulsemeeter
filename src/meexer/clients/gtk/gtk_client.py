from meexer.ipc.client import Client
from meexer.clients.gtk.main_window import blocks
from meexer.schemas.config_schema import ConfigSchema
from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema
from meexer.schemas.app_schema import AppSchema

from meexer.clients.gtk.widgets.device.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
from meexer.clients.gtk.widgets.device.create_device_widget import CreateDevice
from meexer.clients.gtk.services import app_service, device_service

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class GtkClient(Gtk.Application):

    def __init__(self):
        super().__init__(application_id='org.pulsemeeter.meexer')
        self.window = None
        self.client = Client(listen_flags=0, instance_name='gtk')
        res = self.client.send_request('get_config', {})
        self.config = ConfigSchema(**res.data)

        self.device_handlers = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.app_handlers = {'sink_input': {}, 'source_output': {}}
        # self.quit_action = Gio.SimpleAction.new("quit", None)
        # self.quit_action.connect("activate", self.on_shutdown)
        # self.add_action(self.quit_action)

    def create_window(self):
        window = blocks.MainWindow(application=self)
        # window.connect('delete-event', self.on_quit)

        # Connect device creation button press event
        for device_type in ('a', 'b', 'vi', 'hi'):
            add_devices_button = window.device_box[device_type].add_device_button
            add_devices_button.connect('pressed', self.create_new_device_popover, device_type)

        # Load and connect device widget and events
        for device_type, device_id, device in window.load_devices(self.config):
            self.device_handlers[device_type][device_id] = {}
            self.connect_device_gtk_events(device_type, device_id, device)

        # Load app widget
        sink_input_device_list = [device.name for _, device in self.config.vi.items()]
        source_output_device_list = [device.name for _, device in self.config.b.items()]
        source_output_device_list += sink_input_device_list
        app_list = {
            'sink_input': app_service.list_apps('sink_input', self.client),
            'source_output': app_service.list_apps('source_output', self.client)
        }
        window.load_apps(app_list, sink_input_device_list, source_output_device_list)

        # connect events to apps
        for app_type in ('sink_input', 'source_output'):
            for app in window.apps[app_type]:
                self.connect_app_gtk_events(app)

        # window.show_all()
        return window

    def load_devices(self):
        pass

    def do_activate(self, *args, **kwargs):

        # TODO: layouts
        if self.window is None:
            self.window = self.create_window()

        # self.window.connect('destroy', self.on_shutdown)
        self.window.show_all()
        self.window.present()

    def create_new_device_popover(self, widget, device_type):
        '''
            Opens create device popover when clicking on the new device button
        '''
        dt = 'sink' if device_type in ('a', 'vi') else 'source'
        device_list = device_service.list_devices(dt)
        pop = CreateDevice(device_type, device_list)
        pop.create_button.connect('pressed', device_service.create, pop, device_type, device_list)
        pop.create_button.connect('pressed', self.create_button_pressed, pop, device_type)
        pop.set_relative_to(widget)
        pop.popup()

    def create_button_pressed(self, _, popover, device_type):
        '''
            Called when clicking the create device button
        '''

        # create device
        device_id = str(len(self.window.devices[device_type]) + 1)
        device_schema = DeviceSchema(**popover.to_schema())
        device = self.window.insert_device(device_type, device_id, device_schema)
        self.device_handlers[device_type][device_id] = {}
        self.connect_device_gtk_events(device_type, device_id, device, new=True)

    def update_connection_buttons(self, device_type, device_id):
        '''
        Updates all devices connection buttons based on the new added device
            For outputs, it creates the button to it in the inputs
            For input, it creates the connection buttons in itself
        '''

        # new output added
        if device_type in ('a', 'b'):
            for button, input_type, input_id in self.window.update_connection_buttons(device_type, device_id):
                self.connect_output_button(button, input_type, input_id, device_type, device_id)

        # When a new input is added, we gotta create the buttons to existing outputs
        else:
            for button, output_type, output_id in self.window.update_connection_buttons(device_type, device_id):
                self.connect_output_button(button, device_type, device_id, output_type, output_id)

        self.window.show_all()

    def connect_output_button(self, button, input_type, input_id, output_type, output_id):
        device_handle = self.device_handlers[input_type][input_id]

        if output_type not in device_handle:
            device_handle[output_type] = {}

        device_handle[output_type][output_id] = button.connect(
            'toggled', device_service.connect,
            input_type, input_id, output_type, output_id
        )

    def connect_device_gtk_events(self, device_type: str, device_id: str, device: DeviceWidget, new=False):
        '''
        Connect a device widget
        '''

        self.device_handlers[device_type][device_id] = {}
        device_handle = self.device_handlers[device_type][device_id]

        # connect mute signal
        device_handle['mute'] = device.mute_widget.connect(
            'toggled', device_service.mute, device_type, device_id
        )

        # connect volume change signal
        device_handle['volume'] = device.volume_widget.connect(
            'value-changed', device_service.volume, device_type, device_id
        )

        # connect default signal
        device_handle['default'] = device.primary_widget.connect(
            'toggled', device_service.default, device_type, device_id
        )

        # connect change last default device state
        device_handle['default_after'] = device.primary_widget.connect_after(
            'toggled', self.change_default_state, device_type, device_id
        )

        # connect connections widget toggle event
        if device_type in ('hi', 'vi'):
            for output_type in ('a', 'b'):
                for output_id, button in device.connection_buttons[output_type].items():
                    self.connect_output_button(button, device_type, device_id, output_type, output_id)

        # TODO: connect vumeters

        # connect connection buttons
        if new is True:
            self.update_connection_buttons(device_type, device_id)

        return device

    def remove_device(self, device_type: str, device_id: str):
        device = self.window.devices[device_type].pop(device_id)
        self.device_handlers[device_type].pop(device_id)
        self.window.remove_device(device_type, device)
        device.destroy()

    def connect_app_gtk_events(self, app_widget: AppWidget):
        '''
        Create an app widget and add it to an app box
        '''
        # app = AppWidget(app_schema)
        self.app_handlers[app_widget.app_type][app_widget.index] = {}
        app_handler = self.app_handlers[app_widget.app_type][app_widget.index]

        app_handler['volume'] = app_widget.volume.connect(
            'value-changed', app_service.volume, app_widget.app_type, app_widget.index
        )
        app_handler['mute'] = app_widget.mute.connect(
            'toggled', app_service.mute, app_widget.app_type, app_widget.index
        )
        app_handler['combobox'] = app_widget.combobox.connect(
            'changed', app_service.move, app_widget.app_type, app_widget.index
        )
        # TODO: connect vumeter

        # self.apps[app.app_type][app.index] = app

    # def remove_app(self, app_schema: AppSchema):
    #     '''
    #     Delete an app widget
    #     '''
    #     app = self.apps[app_schema.app_type].pop(app_schema.index)
    #     self.app_handlers[app_schema.app_type].pop(app_schema.index)
    #     self.window.remove_app(app)
    #     app.destroy()

    def change_default_state(self, widget, device_type: str, device_id: str):
        '''
        Called after a default request has been sent, removes the previous default
        device as default
        '''

        # disable widget
        widget.set_sensitive(False)

        # search device handler
        for target_id, device in self.window.devices[device_type].items():
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

    def iter_input(self):
        for device_type in ('hi', 'vi'):
            for device_id in self.window.devices[device_type]:
                yield device_type, device_id

    def iter_output(self):
        for device_type in ('a', 'b'):
            for device_id in self.window.devices[device_type]:
                yield device_type, device_id

    def iter_hardware(self):
        for device_type in ('hi', 'a'):
            for device_id in self.window.devices[device_type]:
                yield device_type, device_id

    def iter_virtual(self):
        for device_type in ('vi', 'b'):
            for device_id in self.window.devices[device_type]:
                yield device_type, device_id

    def iter_all(self):
        for device_type in ('vi', 'hi', 'a', 'b'):
            for device_id in self.window.devices[device_type]:
                yield device_type, device_id

    # def on_shutdown(self, _):
        # self.client.send_request('exit', {})
        # self.quit()
        # Gtk.main_quit()
