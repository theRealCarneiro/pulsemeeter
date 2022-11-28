from pulsemeeter.api.audio_client import AudioClient
from pulsemeeter.interface.main_window import MainWindow

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
gi_require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3

from pulsemeeter.interface.devices.virtual_input import VirtualInput
from pulsemeeter.interface.devices.hardware_input import HardwareInput
from pulsemeeter.interface.devices.hardware_output import HardwareOutput
from pulsemeeter.interface.devices.virtual_output import VirtualOutput
from pulsemeeter.interface.devices.app import App

DEVICES = {'vi': VirtualInput, 'hi': HardwareInput, 'a': HardwareOutput, 'b': VirtualOutput}


class WindowController():
    """
    Controls tray, window creation, async update and deletion
    """

    def __init__(self, isserver=False, trayonly=False):
        self.istray = not isserver
        self.trayonly = trayonly
        self.isserver = isserver
        self.devices = {"vi": {}, "hi": {}, "a": {}, "b": {}}
        self.app_list = {"sink-inputs": {}, "source-outputs": {}}
        self.client = AudioClient(listen=True)
        self.config = self.client.config
        self.set_client_callbacks()
        if isserver: self.create_indicator()
        if not trayonly: self.create_window()
        Gtk.main()

    def create_device(self, device_type, device_id):
        """
        Handle device creation popover
        """
        pass

    def init_device(self, device_type, device_id, init=True):
        """
        Init a device in the UI
        """

        device = DEVICES[device_type](self.client, device_type, device_id)

        self.devices[device_type][device_id] = device
        self.main_window.init_device(device_type, device)

    def load_application_list(self, device_type, id=None, app_list=None):
        """
        Load apps into app list
        """
        # if app is not None:
            # self.app_list[device_type][id] = app
            # self.main_window.add_app(app, device_type)
            # return

        if app_list is None:
            app_list = self.client.get_app_list(device_type, id)

        if len(app_list) == 0: return

        for id, label, icon, volume, device in app_list:

            app = App(id, label, icon, volume, device, ['Main', 'Music', 'Comn'])
            app.adjust.connect('value_changed', self.app_volume_change, device_type, id)
            # app.combobox.connect()
            app.show_all()
            self.app_list[device_type][id] = app
            self.main_window.add_app(app, device_type)

    def remove_application(self, device_type, id=None):
        # remove all apps (probably never gonna use it, but still)
        if id is None:
            for id, app in self.app_list[device_type].items():
                self.main_window.remove_app(app, device_type)

        # remove a single app
        if id in self.app_list[device_type]:
            app = self.app_list[device_type][id]
            self.main_window.remove_app(app, device_type)

    def device_new(self, device_type, id,
            label=None, icon=None, volume=None, device=None):
        if device_type == 'sink-inputs' or device_type == 'source-outputs':
            app_list = None if label is None else [(id, label, icon, volume, device)]
            GLib.idle_add(self.load_application_list, device_type, id, app_list)

    def device_remove(self, index, device_type):
        if device_type == 'sink-inputs' or device_type == 'source-outputs':
            GLib.idle_add(self.remove_application, device_type, index)

    def app_volume_change(self, slider, device_type, id):
        """
        Gets called whenever an app volume slider changes
        """
        val = slider.get_value()
        self.client.set_app_volume(id, int(val), device_type[:-1])

    def connect_click(self, button, event, input_type, input_id,
            output_type, output_id):
        """
        Gets called whenever a route button is clicked
        """

        if event.button == 1:
            state = not button.get_active()
            self.client.connect(input_type, input_id,
                    output_type, output_id, state)

        # right click
        elif event.button == 3:
            pass

    def update_conect(self, input_type, input_id, output_type,
            output_id, state, latency=None):
        """
        Callback for conect event in server
        """

        state = state == 'True'
        device = self.devices[input_type][input_id]
        button = device.route_dict[output_type][output_id]
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_mute(self, device_type, device_id, state):
        """
        Callback for mute event in server
        """
        state = state == 'True'
        button = self.devices[device_type][device_id].mute
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_primary(self, device_type, device_id):
        """
        Callback for primary event in server
        """
        for id, button in self.devices[device_type]:
            state = False if id != device_id else True
            GLib.idle_add(button.set_active, state)
            GLib.idle_add(button.set_sensitive, not state)

    def update_volume(self, device_type, device_id, value):
        """
        Callback for volume change event in server
        """
        value = int(value)
        slider = self.devices[device_type][device_id].volume
        curval = slider.get_value()
        if value != curval:
            GLib.idle_add(slider.set_value, value)

    def update_rnnoise(self, device_id, state):
        """
        Callback for mute event in server
        """
        state = state == 'True'
        button = self.devices['hi'][device_id].rnnoise
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_eq(self, device_type, device_id, state):
        """
        Callback for mute event in server
        """
        state = state == 'True'
        button = self.devices[device_type][device_id].eq
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_remove_device(self, device_type, device_id):
        GLib.idle_add(self.main_window.remove_device, device_type,
                      self.devices[device_type][device_id])

        if device_type in ['a', 'b']:
            GLib.idle_add(self.update_loopback_buttons, device_type, device_id, False)

    def update_create_device(self, device_type, device_id, j=None):
        GLib.idle_add(self.init_device, device_type, device_id)
        if device_type in ['a', 'b']:
            GLib.idle_add(self.update_loopback_buttons, device_type, device_id, True)
        GLib.idle_add(self.main_window.window.show_all)

    def update_edit_device(self, device_type, device_id, j):
        self.update_remove_device(device_type, device_id)
        self.update_create_device(device_type, device_id)

    def update_loopback_buttons(self, output_type, output_id, status):
        for input_type in ['hi', 'vi']:
            for input_id, device in self.devices[input_type].items():

                # add
                if status:
                    name_type = 'nick' if output_type == 'a' else 'name'
                    nick = self.config[output_type][output_id][name_type]
                    device.insert_output(output_type, output_id, nick, False)

                # remove
                else:
                    device.remove_output(output_type, output_id)

    def set_client_callbacks(self):
        """
        Set callback for server events
        """
        cb = self.client.set_callback_function

        cb('exit', self.server_exit_event)
        cb('connect', self.update_conect)
        cb('mute', self.update_mute)
        cb('primary', self.update_primary)
        cb('volume', self.update_volume)
        cb('rnnoise', self.update_rnnoise)
        cb('eq', self.update_eq)
        cb('create-device', self.update_create_device)
        cb('remove-device', self.update_remove_device)
        cb('edit-device', self.update_edit_device)
        # cb('change-hd', self.update_device_name)
        cb('device-plugged-in', self.device_new)
        cb('device-unplugged', self.device_remove)

    def create_window(self):
        """
        Create a new instance of the window
        """
        self.main_window = MainWindow(self.client, self.config['layout'])
        window = self.main_window.window
        window.connect('delete_event', self.delete_event)

        for device_type in ['vi', 'hi', 'a', 'b']:
            for device_id in self.config[device_type]:
                self.init_device(device_type, device_id)

        self.load_application_list('sink-inputs')
        self.load_application_list('source-outputs')

        builder = self.main_window.builder
        builder.connect_signals(window)

        window.show_all()

    def delete_window(self):
        """
        Destroy window instance
        """
        window = self.main_window.window
        if window is not None:
            window.destroy

    def create_indicator(self):
        """
        Create tray icon
        """
        indicator = AppIndicator3.Indicator.new(id='pulsemeetertray',
                icon_name='Pulsemeeter',
                category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

        state = self.client.config['tray']
        # state = True
        indicator.set_status(int(state))
        indicator.set_menu(self.tray_menu())
        self.indicator = indicator

    def tray_menu(self):
        """
        Menu to be used in tray module
        """
        menu = Gtk.Menu()

        item_open = Gtk.MenuItem(label='Open Pulsemeeter')
        item_open.connect('activate', self.open_ui)
        menu.append(item_open)

        item_exit = Gtk.MenuItem(label='Close')
        item_exit.connect('activate', self.tray_exit)
        menu.append(item_exit)

        menu.show_all()
        return menu

    def open_ui(self, widget):
        """
        Callback for creating a new window from tray
        """
        try:
            self.main_window.window.present()
        except Exception:
            self.create_window()
            # self.windowinstance = self.start_window(self.isserver)
            # self.trayonly = False

    def toggle_indicator(self, state):
        """
        Set tray visibility
        """
        if state:
            if self.indicator is None:
                self.create_indicator()
            self.indicator.set_status(1)
        else:
            self.indicator.set_status(0)

    def tray_exit(self, widget):
        """
        Exit signal from tray
        """
        self.delete_window()
        self.delete_event()

    def server_exit_event(self, widget=None, event=None):
        """
        Exit signal from server
        """
        self.delete_window()
        Gtk.main_quit()

    def delete_event(self, widget=None, event=None):
        """
        Gets called when the window is destroyed by the user
        """
        if self.isserver and self.indicator.get_status() == 0:
            self.client.close_server()
        else:
            self.client.stop_callbacks()
            self.client.stop_listen()
        for device_type in self.devices:
            for device_id, device in self.devices[device_type].items():
                device.vumeter.close()

        Gtk.main_quit()
