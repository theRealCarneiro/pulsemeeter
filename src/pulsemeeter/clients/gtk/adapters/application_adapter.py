import asyncio
import threading
from pulsectl_asyncio import PulseAsync

from pulsemeeter.scripts.pmctl_async import subscribe_peak
from pulsemeeter.ipc.client import Client

from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.app_manager_model import AppManagerModel
from pulsemeeter.model.device_manager_model import DeviceManagerModel
from pulsemeeter.model.connection_model import ConnectionModel
# from pulsemeeter.schemas.app_schema import AppModel

from pulsemeeter.clients.gtk import layouts
from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
# from pulsemeeter.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup

from pulsemeeter.clients.gtk.services import app_service, device_service

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class ApplicationAdapter(GObject.GObject):
    window: Gtk.Window
    config_model: ConfigModel
    app_manager: AppManagerModel
    vumeter_loop: asyncio.AbstractEventLoop
    vumeter_thread: threading.Thread
    vumeter_tasks: dict[str, dict[str, asyncio.Task]]
    device_handlers: dict[str, dict[str, int]] = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
    model_handlers: dict[str, dict[str, int]] = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
    app_handlers: dict[str, dict[str, int]] = {'sink_input': {}, 'source_output': {}}

    def create_window(self):
        layout = layouts.LAYOUTS[self.config_model.layout]
        self.window = layout.MainWindow(application=self, config_model=self.config_model, app_manager=self.app_manager)

        self.connect_window_gtk_events(self.window)
        self.connect_devicemanager_events()
        for device_type in ('a', 'b', 'hi', 'vi'):
            for device_id, device in self.window.device_box[device_type].devices.items():
                self.connect_device_gtk_events(device_type, device_id, device)

        for app_type in ('sink_input', 'source_output'):
            for app_index, app in self.window.app_box[app_type].apps.items():
                self.connect_app_gtk_events(app_type, app_index, app)

        accel_group = Gtk.AccelGroup()
        self.window.add_accel_group(accel_group)
        self.accel_group = accel_group
        self.current_box = 0
        self.current_device = 0

        accel_group.connect(ord('j'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_box_focus(1))
        accel_group.connect(ord('k'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_box_focus(-1))

        accel_group.connect(ord('h'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_device_focus(-1))
        accel_group.connect(ord('l'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.change_device_focus(1))

        accel_group.connect(ord('m'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('mute', None))
        accel_group.connect(ord('p'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('primary', None))
        accel_group.connect(ord('-'), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('volume', -1))
        accel_group.connect(ord('='), 0, Gtk.AccelFlags.VISIBLE, lambda *args: self.bind_runner('volume', 1))

    #
    # # BINDS
    #

    def bind_runner(self, cmd, arg):
        device_type = self.get_current_kb_device_type()
        device_id = self.get_current_kb_device_id()

        if cmd == 'device_type_cycle':
            self.change_box_focus(arg)
        elif cmd == 'device_cycle':
            self.change_device_focus(arg)
        elif cmd == 'mute':
            self.window.device_box[device_type].devices[device_id].mute_widget.clicked()
        elif cmd == 'primary':
            self.window.device_box[device_type].devices[device_id].primary_widget.clicked()
        elif cmd == 'volume':
            widget = self.window.device_box[device_type].devices[device_id].volume_widget
            widget.set_value(widget.get_value() + arg)
        # elif cmd == 'connect':

    def get_current_kb_device_id(self):
        device_type = self.get_current_kb_device_type()
        current_box = self.window.device_box[device_type]
        device_len = len(current_box.devices)

        if device_len == 0:
            return None

        current_device_key = list(current_box.devices)[self.current_device]
        return current_device_key

    def get_current_kb_device_type(self):
        return list(self.window.device_box)[self.current_box]

    def change_box_focus(self, factor):
        self.current_device = -1
        self.current_box = (self.current_box + factor - 4) % 4
        self.window.device_box[self.get_current_kb_device_type()].focus_box()

    def change_device_focus(self, factor):
        device_type = self.get_current_kb_device_type()
        current_box = self.window.device_box[device_type]
        device_len = len(current_box.devices)
        self.current_device = (self.current_device + factor - device_len) % device_len
        self.focus_device(device_type)

    def focus_device(self, device_type):
        current_box = self.window.device_box[device_type]
        current_box.devices[self.get_current_kb_device_id()].edit_button.grab_focus()

    #
    # # End BINDS
    #

    def update_device_model(self, _, schema, device_type, device_id):
        self.config_model.device_manager.update_device(schema, device_type, device_id)

    # Connect device creation button press event
    def create_new_device_popover(self, widget, device_type):
        '''
            Opens create device popover when clicking on the new device button
        '''
        # get the device type list
        dt = 'sink' if device_type in ('a', 'vi') else 'source'
        # print("CU")
        device_list = device_service.list_devices(dt)

        popover = self.window.device_box[device_type].popover
        if device_type in ('a', 'hi'):
            popover.combobox_widget.empty()
            popover.combobox_widget.load_list(device_list, 'description')

        # connect gtk signals
        popover.confirm_button.connect('clicked', device_service.create, popover, device_type, device_list)
        popover.confirm_button.connect('clicked', self.confirm_button_pressed, popover, device_type)

    def confirm_button_pressed(self, _, popover, device_type):
        '''
            Called when clicking the create device button
        '''
        self.window.create_device(popover.to_schema())

    def start_vumeter(self, app_type, app_name, vumeter_widget, stream_index=None):
        return asyncio.run_coroutine_threadsafe(
            subscribe_peak(app_name, app_type, vumeter_widget.update_peak, stream_index=stream_index),
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

    def connect_devicemanager_events(self):
        self.config_model.device_manager.connect('device_new', self.device_new_callback)
        self.config_model.device_manager.connect('device_remove', self.device_remove_callback)

    def connect_window_gtk_events(self, window):
        window.connect('add_device_pressed', self.add_device_hijack)
        window.connect('device_new', self.device_new)
        window.connect('device_remove', self.device_remove)

    def connect_device_gtk_events(self, device_type: str, device_id: str, device: DeviceWidget):
        '''
        Connect a device widget events to the model
        '''
        # dev_man = self.config_model.device_manager
        device_handler = self.device_handlers[device_type][device_id] = {}

        device_handler['settings'] = device.connect('device_change', self.update_device_model, device_type, device_id)
        device_handler['volume'] = device.connect('volume', self.set_volume, device_type, device_id)
        device_handler['mute'] = device.connect('mute', self.set_mute, device_type, device_id)
        device_handler['connection'] = device.connect('connection', self.set_connection, device_type, device_id)
        device_handler['primary'] = device.connect('primary', self.set_primary, device_type, device_id)

        # self.vumeter_tasks[device_type][device_id] = self.start_vumeter(device)
        pa_device_type = device.device_model.device_type
        vumeter = self.start_vumeter(pa_device_type, device.device_model.name, device.vumeter_widget)
        self.vumeter_tasks[device_type][device_id] = vumeter
        device.connect('destroy', self.stop_vumeter, device_type, device_id)

        # self.connect_callback_functions()

        return device

    def connect_app_gtk_events(self, app_type: str, app_index: str, app: AppWidget):
        '''
        Connect a device widget events to the model
        '''
        app_handler = self.app_handlers[app_type][app_index] = {}

        app_handler['app_volume'] = app.connect('app_volume', self.set_app_volume, app_type, app_index)
        app_handler['app_mute'] = app.connect('app_mute', self.set_app_mute, app_type, app_index)
        app_handler['app_device'] = app.connect('app_device_change', self.set_app_device, app_type, app_index)

        stream_type = app_type.split('_')[0]
        vumeter = self.start_vumeter(stream_type, app.app_model.device, app.vumeter, app.app_model.index)
        self.vumeter_tasks[app_type][app_index] = vumeter

        app.connect('destroy', self.stop_vumeter, app_type, app_index)

        return app

    def connect_device_model_events(self, device_type: str, device_id: str, device: DeviceModel):
        '''
        Connect a device widget
        '''
        win_man = self.window.device
        model_handler = self.model_handlers[device_type][device_id]

        model_handler['volume'] = device.connect('volume', win_man.set_volume)
        model_handler['mute'] = device.connect('mute', win_man.set_mute)
        model_handler['connection'] = device.connect('connection', win_man.set_connection)
        model_handler['primary'] = device.connect('primary')

        # self.vumeter_tasks[device_type][device_id] = self.start_vumeter(device.device_type, device.name, device.vumeter)
        # device.connect('destroy', self.stop_vumeter, device_type, device_id)

        # self.connect_callback_functions()

        return device

    #
    # # Update model functions
    #
    def set_volume(self, _, volume: int, device_type, device_id):
        '''
        Set model volume
        '''
        self.config_model.device_manager.set_volume(device_type, device_id, volume)

    def set_mute(self, _, state: bool, device_type, device_id):
        '''
        Set model mute
        '''
        self.config_model.device_manager.set_mute(device_type, device_id, state)

    def set_primary(self, _, state, device_type, device_id):
        '''
        Set model primary
        '''
        self.config_model.device_manager.set_primary(device_type, device_id)
        for target_id, target_device in self.window.device_box[device_type].devices.items():
            if target_id != device_id:
                target_device.set_primary(False)

    def set_connection(self, _, output_type, output_id, state: bool, input_type, input_id):
        '''
        Set model connection
        '''
        self.config_model.device_manager.set_connection(input_type, input_id, output_type, output_id, state)

    def device_new(self, _, device_schema):
        '''
        Add new device to model
        '''
        device_type, device_id, device = self.config_model.device_manager.create_device(device_schema)
        if device.device_class != 'virtual':
            return

        if device_schema.device_type == 'sink':
            AppCombobox.append_device_list('sink_input', device_schema.name)
            AppCombobox.append_device_list('source_output', device_schema.name + '.monitor')
        else:
            AppCombobox.append_device_list('source_output', device_schema.name)

    def device_remove(self, _, device_type, device_id):
        '''
        Remove model device
        '''
        device_schema = self.config_model.device_manager.get_device(device_type, device_id)
        self.config_model.device_manager.remove_device(device_type, device_id)

        if device_schema.device_type == 'sink':
            AppCombobox.append_device_list('sink_input', device_schema.name)
            AppCombobox.append_device_list('source_output', device_schema.name + '.monitor')
        else:
            AppCombobox.append_device_list('source_output', device_schema.name)

    def add_device_hijack(self, _, device_type):
        if device_type not in ('a', 'hi'):
            return

        device_list = DeviceManagerModel.list_devices(device_type)
        self.window.device_box[device_type].popover.device_list = device_list
        self.window.device_box[device_type].popover.combobox_widget.load_list(device_list, 'description')

    def set_app_volume(self, _, volume: int, app_type, app_index):
        '''
        Set model volume
        '''
        self.app_manager.set_volume(app_type, app_index, volume)

    def set_app_mute(self, _, state: bool, app_type, app_index):
        '''
        Set model mute
        '''
        self.app_manager.set_mute(app_type, app_index, state)

    def set_app_device(self, _, device_name: str, app_type, app_index):
        '''
        Set model device
        '''
        self.app_manager.change_device(app_type, app_index, device_name)

    #
    # # End model update functions
    #

    #
    # # Model Callback functions
    #
    def device_new_callback(self, device_type, device_id, device):
        device_widget = self.window.create_device(device_type, device_id, device)
        self.connect_device_gtk_events(device_type, device_id, device_widget)

    def device_remove_callback(self, device_type: str, device_id: str):
        self.window.device_box[device_type].remove_device(device_id)
        self.device_handlers[device_type].pop(device_id)
    #
    # # End Model Callback functions
    #

    def iter_input(self):
        for device_type in ('hi', 'vi'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_output(self):
        for device_type in ('a', 'b'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_hardware(self):
        for device_type in ('hi', 'a'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_virtual(self):
        for device_type in ('vi', 'b'):
            for device_id, device_widget in self.window.device_box[device_type].devices.items():
                yield device_type, device_id, device_widget

    def iter_all(self):
        for device_type, device_box in self.window.device_box.items():
            for device_id, device_widget in device_box.devices.items():
                yield device_type, device_id, device_widget
