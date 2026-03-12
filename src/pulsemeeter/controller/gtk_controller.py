import logging
import asyncio
import traceback
import threading

from concurrent.futures._base import CancelledError
from pulsemeeter.scripts import pmctl
from pulsemeeter.scripts.pmctl_async import subscribe_peak

from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.app_model import AppModel

from pulsemeeter.clients.gtk.layouts import layout_manager
# from pulsemeeter.clients.gtk import layouts
from pulsemeeter.clients.gtk.widgets.content import Content
from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget
from pulsemeeter.clients.gtk.widgets.app.app_dropdown import AppDropDown
# from pulsemeeter.settings import STYLE_FILE

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")


class GtkController(SignalModel):
    '''
    GtkController emits signals for UI and application actions.

    Signals:
        volume(device_type: str, device_id: str, volume: int):
            Emitted when a device's volume is changed.
        mute(device_type: str, device_id: str, state: bool):
            Emitted when a device's mute state is changed.
        primary(device_type: str, device_id: str):
            Emitted when a device is set as primary.
        connect(input_type: str, input_id: str, output_type: str, output_id: str, state: bool):
            Emitted when a connection between devices is changed.
        connection_change(input_type: str, input_id: str, output_type: str, output_id: str, connection_model):
            Emitted when a connection model is updated.
        device_new(device_model):
            Emitted when a new device is created.
        device_remove(device_type: str, device_id: str):
            Emitted when a device is removed.
        device_change(schema, device_type: str, device_id: str):
            Emitted when a device's settings are updated.
        app_volume(app_type: str, app_index: str, volume: int):
            Emitted when an application's volume is changed.
        app_mute(app_type: str, app_index: str, state: bool):
            Emitted when an application's mute state is changed.
        app_device(app_type: str, app_index: str, device_nick: str):
            Emitted when an application's device is changed.
    '''

    window: Gtk.Window
    config_model: ConfigModel
    vumeter_loop: asyncio.AbstractEventLoop
    vumeter_thread: threading.Thread

    vumeter_tasks: dict[str, dict[str, asyncio.Task]]
    device_handlers: dict[str, dict[str, int]]
    model_handlers: dict[str, dict[str, int]]
    app_handlers: dict[str, dict[str, int]]

    def __init__(self, device_repository):

        super().__init__()

        self.device_repository = device_repository
        self.config_model = device_repository.config

        # create vumeter loop thread
        self.vumeter_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.vumeter_thread = threading.Thread(target=self.vumeter_loop.run_forever, daemon=True)
        self.vumeter_thread.start()

        self.window = None
        self.content = None
        self.vumeter_tasks = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}, 'sink_input': {}, 'source_output': {}}
        self.device_handlers = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.app_handlers = {'sink_input': {}, 'source_output': {}}

    def create_window(self, application):
        # layout = layouts.LAYOUTS[self.config_model.layout]
        # self.window = layout.MainWindow(application=application)

        self.create_content(self.config_model.layout)
        self.window = Gtk.Window(title='Pulsemeeter', application=application)
        self.window.set_default_size(self.config_model.window_width, self.config_model.window_height)
        self.window.set_child(self.content)
        self.connect_window_gtk_events()

        self.load_device_list()
        self.load_app_list()
        return self.window

    def create_content(self, layout):
        arrange_content = layout_manager.get_arrange_content(layout)
        self.content = Content()
        arrange_content(self.content)

        # arrange_device_popover = layout_manager.get_arrange_device_settings(layout)
        # for device_type in ('a', 'b', 'vi', 'hi'):
        #     popover = self.content.create_device_button[device_type].get_popover()
        #     arrange_device_popover(popover)

        self.connect_content_gtk_events()
        self.content.settings_box.fill_settings(self.config_model)
        return self.content

    def create_device_widget(self, device_type, device_id, device_model, refresh=False):
        '''
        Insert a device widget and add it to a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to insert in the box
        '''
        arrange_device = layout_manager.get_arrange_device(self.config_model.layout)
        device_widget = DeviceWidget(device_model)
        arrange_device(device_widget)
        # arrange_device_settings(device_widget.popover)
        self.content.device_box[device_type].add_widget(device_id, device_widget)
        self.connect_device_gtk_events(device_type, device_id, device_widget)
        self.append_app_combobox(device_model)

        if refresh:
            self.reload_connection_widgets()

        return device_widget

    def remove_device_widget(self, device_type, device_id, refresh=False):
        '''
        Destroy a device widget and remove it from a device box
            "device_type" is [vi, hi, a, b]
            "device" is the device widget to remove from the box
        '''
        device_widget = self.content.device_box[device_type].remove_widget(device_id)
        self.pop_app_combobox(device_widget.device_model)
        device_widget.run_dispose()

        if refresh:
            self.reload_connection_widgets()

        return device_widget

    def change_device_widget(self, device_type, device_id, device_model):
        device_widget = self.content.device_box[device_type].widgets[device_id]
        device_widget.fill_settings()
        self.reload_connection_widgets()
        self.append_app_combobox(device_model)

    def on_device_widget_destroy(self, _, device_type, device_id):
        if device_id in self.vumeter_tasks.get(device_type, {}):
            self.stop_vumeter(device_type, device_id)
        self.device_handlers[device_type].pop(device_id, None)

    def on_app_widget_destroy(self, _, app_type, app_id):
        if app_id in self.vumeter_tasks.get(app_type, {}):
            self.stop_vumeter(app_type, app_id)
        self.app_handlers[app_type].pop(app_id, None)

    def on_window_destroy(self, _):
        '''
        Called when the main window gets destroyed
        '''
        width, height = self.window.get_default_size()
        self.config_model.window_width = width
        self.config_model.window_height = height

    def reload_connection_widgets(self):
        '''
        Reloads all connection widgets
        '''
        for device_type in ('hi', 'vi'):
            for _, device in self.content.device_box[device_type].widgets.items():
                device.reload_connection_widgets()

    def create_app_widget(self, app_type, app_index, app_model):
        '''
        Create a new app widget from a model, insert it and return it
        '''
        arrange_app = layout_manager.get_arrange_app(self.config_model.layout)
        app_widget = AppWidget(app_model)
        arrange_app(app_widget)
        self.content.app_box[app_type].add_widget(app_index, app_widget)
        self.connect_app_gtk_events(app_type, app_index, app_widget)
        return app_widget

    def remove_app_widget(self, app_type, app_index):
        '''
        Remove app widget and return it
        '''
        app_widget = self.content.app_box[app_type].remove_widget(app_index)
        if app_widget:
            app_widget.run_dispose()
        return app_widget

    def load_device_list(self):
        '''
        Load the devices from config
        '''
        for device_type, device_dict in self.device_repository.get_all_devices().items():
            for device_id, device_model in device_dict.items():
                self.create_device_widget(device_type, device_id, device_model)

    def load_app_list(self):
        '''
        Load the current available pulseaudio sink inputs and source outputs
        '''

        self.load_app_combobox()

        for app_type in ('sink_input', 'source_output'):
            for app_index, app_model in self.list_apps(app_type).items():
                self.create_app_widget(app_type, app_index, app_model)

    def list_apps(self, app_type: str) -> dict[str, AppModel]:
        '''
        Returns a list of AppModels
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        pa_app_list = pmctl.list_apps(app_type)

        app_dict = {}
        for app in pa_app_list:
            app = AppModel.pa_to_app_model(app, app_type)
            app_dict[app.index] = app

        return app_dict

    def load_app_combobox(self):
        self.block_app_combobox_handlers(True)
        sink_input_device_list = [('', '')]
        source_output_device_list = [('', '')]

        for device in self.device_repository.get_devices_by_type('vi').values():
            sink_input_device_list.append((device.nick, device.name))
            source_output_device_list.append((device.nick + '.monitor', device.name))

        for device in self.device_repository.get_devices_by_type('b').values():
            source_output_device_list.append((device.nick, device.name))

        AppDropDown.set_device_list('sink_input', sink_input_device_list)
        AppDropDown.set_device_list('source_output', source_output_device_list)
        self.block_app_combobox_handlers(False)

    def append_app_combobox(self, device):
        self.block_app_combobox_handlers(True)
        if device.device_type == 'sink':
            AppDropDown.append_device_list('sink_input', (device.nick, device.name))
            AppDropDown.append_device_list('source_output', (device.nick + '.monitor', device.name))
        else:
            AppDropDown.append_device_list('source_output', (device.nick, device.name))
        self.block_app_combobox_handlers(False)

    def pop_app_combobox(self, device):
        self.block_app_combobox_handlers(True)
        if device.device_type == 'sink':
            AppDropDown.remove_device_list('sink_input', (device.nick, device.name))
            AppDropDown.remove_device_list('source_output', (device.nick + '.monitor', device.name))
        else:
            AppDropDown.remove_device_list('source_output', (device.nick, device.name))
        self.block_app_combobox_handlers(False)

    def block_app_combobox_handlers(self, state):
        for app_type in ('sink_input', 'source_output'):
            for app_index, app in self.content.app_box[app_type].widgets.items():
                handler = self.app_handlers[app_type][app_index]['app_device']
                if state:
                    app.handler_block(handler)
                else:
                    app.handler_unblock(handler)

    def settings_menu_open(self, _):
        self.content.settings_box.fill_settings(self.config_model)

    def settings_menu_apply(self, _, config_schema):
        vumeters_changed = self.config_model.vumeters != config_schema['vumeters']
        self.config_model.vumeters = config_schema['vumeters']
        self.config_model.cleanup = config_schema['cleanup']
        self.config_model.tray = config_schema['tray']
        layout_changed = self.config_model.layout != config_schema['layout']
        self.config_model.layout = config_schema['layout']
        if layout_changed:
            self.rebuild_content()
        elif vumeters_changed:
            if self.config_model.vumeters:
                self.start_all_vumeters()
            else:
                self.stop_all_vumeters()

    def stop_all_vumeters(self):
        for device_type in ('a', 'b', 'vi', 'hi'):
            for task in self.vumeter_tasks[device_type].values():
                task.cancel()
            self.vumeter_tasks[device_type].clear()
            for device_widget in self.content.device_box[device_type].widgets.values():
                device_widget.vumeter_widget.set_fraction(0)
        for app_type in ('sink_input', 'source_output'):
            for task in self.vumeter_tasks[app_type].values():
                task.cancel()
            self.vumeter_tasks[app_type].clear()
            for app_widget in self.content.app_box[app_type].widgets.values():
                app_widget.vumeter_widget.set_fraction(0)

    def start_all_vumeters(self):
        for device_type in ('a', 'b', 'vi', 'hi'):
            for device_id, device_widget in self.content.device_box[device_type].widgets.items():
                pa_device_type = device_widget.device_model.device_type
                vumeter = self.start_vumeter(pa_device_type, device_widget.device_model.name, device_widget.vumeter_widget)
                self.vumeter_tasks[device_type][device_id] = vumeter
        for app_type in ('sink_input', 'source_output'):
            for app_index, app_widget in self.content.app_box[app_type].widgets.items():
                stream_type = app_type.split('_')[0]
                vumeter = self.start_vumeter(stream_type, app_widget.app_model.label + str(app_widget.app_model.index), app_widget.vumeter_widget, app_index)
                self.vumeter_tasks[app_type][app_index] = vumeter

    def rebuild_content(self):
        self.stop_all_vumeters()

        # Clear handler references (old widgets being destroyed)
        for device_type in ('a', 'b', 'vi', 'hi'):
            self.device_handlers[device_type].clear()
        for app_type in ('sink_input', 'source_output'):
            self.app_handlers[app_type].clear()

        # Build new content with the new layout and swap it in
        self.create_content(self.config_model.layout)
        self.window.set_child(self.content)

        # Repopulate all device and app widgets
        self.load_device_list()
        self.load_app_list()

    def connect_window_gtk_events(self):
        '''
        Connect window events to the model
        '''

        signal_map = {
            # 'add_device_pressed': self.add_device_hijack,
            # 'device_new': self.device_new,
            # 'settings_change': self.settings_menu_apply,
            'close-request': self.on_window_destroy
        }

        for signal_name, callback in signal_map.items():
            self.window.connect(signal_name, callback)

    def connect_device_gtk_events(self, device_type: str, device_id: str, device: DeviceWidget):
        '''
        Connect a device widget events to the model
        '''

        signal_map = {
            'volume': self.set_volume,
            'mute': self.set_mute,
            'connection': self.set_connection,
            'primary': self.set_primary,
            'device_change': self.update_device_model,
            'device_remove': self.device_remove,
            'update_connection': self.update_connection,
            'destroy': self.on_device_widget_destroy,
            'settings_pressed': self.add_device_hijack,
            'connection_settings_pressed': self.connection_settings_hijack,
        }

        device_handler = self.device_handlers[device_type][device_id] = {}
        for signal_name, callback in signal_map.items():
            device_handler[signal_name] = device.connect(signal_name, callback, device_type, device_id)

        pa_device_type = device.device_model.device_type
        if self.config_model.vumeters:
            vumeter = self.start_vumeter(pa_device_type, device.device_model.name, device.vumeter_widget)
            self.vumeter_tasks[device_type][device_id] = vumeter

        return device

    def connect_content_gtk_events(self):
        signal_map = {
            'add_device_pressed': self.add_device_hijack,
            'device_new': self.device_new,
            'settings_pressed': self.settings_menu_open,
            'settings_change': self.settings_menu_apply,
        }

        for signal_name, callback in signal_map.items():
            self.content.connect(signal_name, callback)

    # def connect_connection_gtk_events(self, input_type, input_id, output_type, output_id):
    #     pass

    def connect_app_gtk_events(self, app_type: str, app_index: str, app: AppWidget):
        '''
        Connect a device widget events to the model
        '''

        signal_map = {
            'app_volume': self.set_app_volume,
            'app_mute': self.set_app_mute,
            'app_device': self.set_app_device,
            'destroy': self.on_app_widget_destroy
        }

        # connect gtk signals to callbacks
        app_handler = self.app_handlers[app_type][app_index] = {}
        for signal_name, callback in signal_map.items():
            app_handler[signal_name] = app.connect(signal_name, callback, app_type, app_index)

        # start vumeter
        stream_type = app_type.split('_')[0]
        if self.config_model.vumeters:
            vumeter = self.start_vumeter(stream_type, app.app_model.label + str(app.app_model.index), app.vumeter_widget, app_index)
            self.vumeter_tasks[app_type][app_index] = vumeter

        return app

    def connection_settings_hijack(self, device_widget, output_type, output_id, input_type, input_id):
        '''
        Populates the device combobox every time the popup opens, so that the
        devices are always up to date
        '''
        input_model = self.device_repository.get_device(input_type, input_id)
        output_model = self.device_repository.get_device(output_type, output_id)
        # connection_model = input_model.connections[output_type][output_id]
        button = device_widget.connections_widgets[output_type].get_widget(output_id)
        button.popover.fill_settings()
        button.popover.port_map_widget.clear_port_map()
        button.popover.port_map_widget.create_routing_grid(input_model, output_model)

    def add_device_hijack(self, _, settings_widget, device_type, device_id):
        '''
        Populates the device combobox every time the popup opens, so that the
        devices are always up to date
        '''

        if device_type in ('a', 'hi'):
            device_list = self.list_devices(device_type)
            settings_widget.combobox_widget.empty()
            settings_widget.combobox_widget.load_list(device_list, 'description')

        if device_id:
            device_model = self.device_repository.get_device(device_type, device_id)
            settings_widget.fill_settings(device_model)

    def list_devices(self, device_type):
        '''
        List devices of a given type.
        Args:
            device_type (str): Type of device ('a' for sink, 'b' for source).
        Returns:
            list: List of DeviceModel objects.
        '''
        dvtp = 'sink' if device_type == 'a' else 'source'
        pa_device_list = pmctl.list_devices(dvtp)
        device_list = []
        for device in pa_device_list:
            device_model = DeviceModel.pa_to_device_model(device, dvtp)
            device_list.append(device_model)
        return device_list

    def handle_vumeter_error(self, fut):
        try:
            fut.result()

        except CancelledError:
            LOG.debug("VUmeter task canceled")

        except Exception as e:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            LOG.error("Vumeter task error: \n %s", tb_str)

    def start_vumeter(self, app_type, app_name, vumeter_widget, stream_index=None):
        future = asyncio.run_coroutine_threadsafe(
            subscribe_peak(app_name, app_type, vumeter_widget.update_peak, stream_index=stream_index),
            self.vumeter_loop
        )

        future.add_done_callback(self.handle_vumeter_error)
        return future

    def stop_vumeter(self, device_type, device_id):
        if not self.config_model.vumeters:
            return

        self.vumeter_tasks[device_type][device_id].cancel()
        del self.vumeter_tasks[device_type][device_id]

    #
    # # Update model functions
    #
    def set_volume(self, _, volume: int, device_type, device_id):
        '''
        Set model volume
        '''
        self.emit('volume', device_type, device_id, volume)

    def set_mute(self, _, state: bool, device_type, device_id):
        '''
        Set model mute
        '''
        self.emit('mute', device_type, device_id, state)

    def set_primary(self, _, device_type, device_id):
        '''
        Set model primary
        '''
        for target_id, target_device in self.content.device_box[device_type].widgets.items():
            if target_id != device_id:
                target_device.primary_widget.set_primary(False)
        self.emit('primary', device_type, device_id)

    def set_connection(self, _, output_type, output_id, state: bool, input_type, input_id):
        '''
        Call to device model to set model connection
        '''
        self.emit('connect', input_type, input_id, output_type, output_id, state)

    def update_connection(self, _, output_type, output_id, connection_model, input_type, input_id):
        '''
        Call to device model to set model connection
        '''
        self.emit('connection_change', input_type, input_id, output_type, output_id, connection_model)

    def device_new(self, _, device_model):
        '''
        Call to device model to create new device model
        '''
        self.emit('device_new', device_model)

    def device_remove(self, _, device_type, device_id):
        '''
        Call device manager to remove device model
        '''
        self.emit('device_remove', device_type, device_id)

    def update_device_model(self, _, schema, device_type, device_id):
        '''
        Call to device model to update a device settings
        '''
        self.emit('device_change', schema, device_type, device_id)

    def set_app_volume(self, _, volume: int, app_type, app_index):
        '''
        Set model volume
        '''
        self.emit('app_volume', app_type, app_index, volume)

    def set_app_mute(self, _, state: bool, app_type, app_index):
        '''
        Set model mute
        '''
        self.emit('app_mute', app_type, app_index, state)

    def set_app_device(self, _, device_nick: str, app_type, app_index):
        '''
        Set model device
        '''
        self.emit('app_device', app_type, app_index, device_nick)

    #
    # # End model update functions
    #

    #
    # # Model Callback functions
    #
    def device_new_callback(self, device_type, device_id, device_model):
        def wrapper():
            device = self.create_device_widget(device_type, device_id, device_model, refresh=True)
            return False

        GLib.idle_add(wrapper)

    def device_remove_callback(self, device_type: str, device_id: str):
        def wrapper():
            self.remove_device_widget(device_type, device_id, refresh=True)
            return False

        GLib.idle_add(wrapper)

    def device_change_callback(self, device_type: str, device_id: str, device_model):
        def wrapper():
            self.change_device_widget(device_type, device_id, device_model)
            return False

        GLib.idle_add(wrapper)

    def pa_device_change_callback(self, device_type: str, device_id: str, device_model: DeviceModel):
        def wrapper():
            device_widget = self.content.device_box[device_type].widgets[device_id]
            device_widget.pa_device_change()
            return False

        GLib.idle_add(wrapper)

    def pa_primary_change_callback(self, device_type: str, device_id: str):
        def wrapper():
            for target_id, target_device in self.content.device_box[device_type].widgets.items():
                target_device.primary_widget.set_primary(target_id == device_id)

            return False

        GLib.idle_add(wrapper)

    def app_new_callback(self, app_type: str, app_index: int, app_model: DeviceModel):
        def wrapper():
            app = self.create_app_widget(app_type, app_index, app_model)
            return False

        GLib.idle_add(wrapper)

    def app_remove_callback(self, app_type: str, app_index: int):
        def wrapper():
            self.remove_app_widget(app_type, app_index)
            return False

        GLib.idle_add(wrapper)

    def app_change_callback(self, app_type: str, app_index: int, app: DeviceModel):
        def wrapper():
            app_widget = self.content.app_box[app_type].widgets.get(app_index)
            if app_widget:
                app_widget.pa_app_change(app)
            return False

        GLib.idle_add(wrapper)

    #
    # # End Model Callback functions
    #

    #
    # # BINDS
    #

    # def add_accels(self):
        # accel_group = Gtk.AccelGroup()
        # self.window.add_accel_group(accel_group)
        # self.accel_group = accel_group
        # self.current_box = 0
        # self.current_device = 0
        #
        # accel_group.connect(ord('j'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_box_focus(1))
        # accel_group.connect(ord('k'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_box_focus(-1))
        #
        # accel_group.connect(ord('h'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_device_focus(-1))
        # accel_group.connect(ord('l'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_device_focus(1))
        #
        # accel_group.connect(ord('m'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('mute', None))
        # accel_group.connect(ord('p'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('primary', None))
        # accel_group.connect(ord('-'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('volume', -1))
        # accel_group.connect(ord('='), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('volume', 1))

    def bind_runner(self, cmd, arg):
        device_type = self.get_current_kb_device_type()
        device_id = self.get_current_kb_device_id()

        if cmd == 'device_type_cycle':
            self.change_box_focus(arg)
        elif cmd == 'device_cycle':
            self.change_device_focus(arg)
        elif cmd == 'mute':
            self.content.device_box[device_type].widgets[device_id].mute_widget.clicked()
        elif cmd == 'primary':
            self.content.device_box[device_type].widgets[device_id].primary_widget.clicked()
        elif cmd == 'volume':
            widget = self.content.device_box[device_type].widgets[device_id].volume_widget
            widget.set_value(widget.get_value() + arg)
        # elif cmd == 'connect':

    def get_current_kb_device_id(self):
        device_type = self.get_current_kb_device_type()
        current_box = self.content.device_box[device_type]
        device_len = len(current_box.widgets)

        if device_len == 0:
            return None

        current_device_key = list(current_box.widgets)[self.current_device]
        return current_device_key

    def get_current_kb_device_type(self):
        return list(self.content.device_box)[self.current_box]

    def change_box_focus(self, factor):
        self.current_device = -1
        self.current_box = (self.current_box + factor - 4) % 4
        self.content.device_box[self.get_current_kb_device_type()].focus_box()

    def change_device_focus(self, factor):
        device_type = self.get_current_kb_device_type()
        current_box = self.content.device_box[device_type]
        device_len = len(current_box.widgets)
        self.current_device = (self.current_device + factor - device_len) % device_len
        self.focus_device(device_type)

    def focus_device(self, device_type):
        current_box = self.content.device_box[device_type]
        current_box.widgets[self.get_current_kb_device_id()].edit_button.grab_focus()

    #
    # # End BINDS
    #
