import asyncio
import threading

from meexer.ipc.client import Client
from meexer.clients.gtk.main_window import blocks
from meexer.schemas.config_schema import ConfigSchema
from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema
# from meexer.schemas.app_schema import AppSchema
from meexer.scripts.pmctl_async import subscribe_peak

from meexer.clients.gtk.widgets.device.device_widget import DeviceWidget
from meexer.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
from meexer.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup
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

        # create client and get config
        self.client = Client(listen_flags=0, instance_name='gtk')
        res = self.client.send_request('get_config', {})
        self.config = ConfigSchema(**res.data)

        # create vumeter loop thread
        self.vumeter_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.vumeter_thread = threading.Thread(target=self.vumeter_loop.run_forever, daemon=True)
        self.vumeter_thread.start()

        self.vumeter_tasks = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.device_handlers = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.app_handlers = {'sink_input': {}, 'source_output': {}}

    def do_activate(self, *args, **kwargs):

        # TODO: layouts
        if self.window is None:
            self.create_window()

        self.window.connect('destroy', self.on_shutdown)
        self.window.show_all()
        self.window.present()

    def create_window(self):
        self.window = blocks.MainWindow(application=self, config_schema=self.config)
        # window.connect('delete-event', self.on_quit)

        self.connect_device_creation_buttons()
        self.connect_device_widgets()

        # Load app widget
        # sink_input_device_list = [device.name for _, device in self.config.vi.items()]
        # source_output_device_list = [device.name for _, device in self.config.b.items()]
        # source_output_device_list += sink_input_device_list
        # app_list = {
        #     'sink_input': app_service.list_apps('sink_input', self.client),
        #     'source_output': app_service.list_apps('source_output', self.client)
        # }
        # window.load_apps(app_list, sink_input_device_list, source_output_device_list)
        #
        # # connect events to apps
        # for app_type in ('sink_input', 'source_output'):
        #     for app in window.apps[app_type]:
        #         self.connect_app_gtk_events(app)

        # window.show_all()
        # return window

    # Connect device creation button press event
    def connect_device_creation_buttons(self):
        for device_type in ('a', 'b', 'vi', 'hi'):
            add_devices_button = self.window.device_box[device_type].add_device_button
            add_devices_button.connect_after('pressed', self.create_new_device_popover, device_type)

    def connect_device_widgets(self):
        # Load and connect device widget and events
        for device_type, device_id, device_widget in self.iter_all():
            self.connect_device_gtk_events(device_type, device_id, device_widget)

    def create_new_device_popover(self, widget, device_type):
        '''
            Opens create device popover when clicking on the new device button
        '''
        # get the device type list
        dt = 'sink' if device_type in ('a', 'vi') else 'source'
        device_list = device_service.list_devices(dt)

        popover = self.window.device_box[device_type].popover
        if device_type in ('a', 'hi'):
            popover.combobox_widget.empty()
            popover.combobox_widget.load_list(device_list, 'description')

        # connect gtk signals
        popover.confirm_button.connect('pressed', device_service.create, popover, device_type, device_list)
        popover.confirm_button.connect('pressed', self.confirm_button_pressed, popover, device_type)

    def confirm_button_pressed(self, _, popover, device_type):
        '''
            Called when clicking the create device button
        '''

        device_id = str(len(self.window.device_box[device_type].devices) + 1)

        # initialize connections schema
        preschema = popover.to_schema()
        preschema['connections'] = self.create_connections_schema(device_type)

        # create device
        device_schema = DeviceSchema(**preschema)
        device = self.window.insert_device(device_type, device_id, device_schema)
        if device_type in ('a', 'b'):
            self.update_connection_buttons(device_type, device_id)

        self.connect_device_gtk_events(device_type, device_id, device, new=True)

    def create_connections_schema(self, device_type) -> dict[str, dict[str, ConnectionSchema]]:
        '''
            Returns a dict with the connection schemas to existing devices
            To be used when a new device is created
        '''

        if device_type in ('a', 'b'):
            return {}

        connections_schema = {'a': {}, 'b': {}}
        for output_type, output_id, device_widget in self.iter_output():
            connection_schema = ConnectionSchema(nick=device_widget.nick)
            connections_schema[output_type][output_id] = connection_schema

        # for output_type in ('a', 'b'):
            # for output_id, device_widget in self.window.device_box[device_type].devices.items():
                # connection_schema = ConnectionSchema(nick=device_widget.nick)
                # connections_schema[output_type][output_id] = connection_schema

        return connections_schema

    def update_connection_buttons(self, device_type, device_id):
        '''
        Called when a new output is added (a, b)
            Add Connection widget to input devices (vi, hi)
        '''

        if device_type in ('vi', 'hi'):
            return

        # new output added, gotta create buttons to it in existing inputs
        device_nick = self.window.device_box[device_type].devices[device_id].get_nick()
        connection_schema = ConnectionSchema(nick=device_nick)

        for input_type, input_id, input_widget in self.iter_input():
            button = input_widget.insert_connection_widget(connection_schema, device_type, device_id)
            self.connect_output_button(button, input_type, input_id, device_type, device_id)

        self.window.show_all()

    def connect_connection_widgets_gtk_events(self, device_type, device_id):
        device = self.window.device_box[device_type].devices[device_id]

        for output_type, box in device.connections_box.items():
            for output_id, button in box.connection_widgets.items():
                self.connect_output_button(button, device_type, device_id, output_type, output_id)

    def connect_output_button(self, button, input_type, input_id, output_type, output_id):
        device_handle = self.device_handlers[input_type][input_id]

        if output_type not in device_handle:
            device_handle[output_type] = {}

        device_handle[output_type][output_id] = button.connect(
            'toggled', device_service.connect,
            input_type, input_id, output_type, output_id
        )

    def start_vumeter(self, device: DeviceWidget):
        return asyncio.run_coroutine_threadsafe(
            subscribe_peak(device.schema.name, device.schema.device_type, device.vumeter_widget.update_peak, rate=24),
            self.vumeter_loop
        )

    def stop_vumeter(self, _, device_type, device_id):
        self.vumeter_tasks[device_type][device_id].cancel()

    def edit_device_popover_confirm(self, _, device_type, device_id):
        # get the device type list
        dt = 'sink' if device_type in ('a', 'vi') else 'source'
        device_list = device_service.list_devices(dt) if device_type in ('a', 'hi') else []

        popover = self.window.device_box[device_type].devices[device_id].popover
        if device_type in ('a', 'hi'):
            popover.combobox_widget.empty()
            popover.combobox_widget.load_list(device_list, 'description')

    def connect_device_gtk_events(self, device_type: str, device_id: str, device: DeviceWidget, new=False):
        '''
        Connect a device widget
        '''

        self.device_handlers[device_type][device_id] = {}
        device_handle = self.device_handlers[device_type][device_id]
        device.edit_button.connect_after('pressed', self.edit_device_popover_confirm, device_type, device_id)

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
        self.connect_connection_widgets_gtk_events(device_type, device_id)
        # for output_type, box in device.connections_box.items():
        #     for output_id, button in box.connection_widgets.items():
        #         self.connect_output_button(button, device_type, device_id, output_type, output_id)

        self.vumeter_tasks[device_type][device_id] = self.start_vumeter(device)
        device.connect('destroy', self.stop_vumeter, device_type, device_id)

        return device

    def remove_device(self, device_type: str, device_id: str):
        self.window.device_box[device_type].remove_device(device_id)
        self.device_handlers[device_type].pop(device_id)

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
        for target_id, device in self.window.device_box[device_type].devices.items():
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
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id

    def iter_output(self):
        for device_type in ('a', 'b'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_hardware(self):
        for device_type in ('hi', 'a'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id

    def iter_virtual(self):
        for device_type in ('vi', 'b'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_all(self):
        for device_type, device_box in self.window.device_box.items():
            for device_id, device_widget in device_box.devices.items():
                yield device_type, device_id, device_widget

    def on_shutdown(self, _):
        # cancel vumeters
        for device_type, device_id, _ in self.iter_all():
            self.vumeter_tasks[device_type][device_id].cancel()
