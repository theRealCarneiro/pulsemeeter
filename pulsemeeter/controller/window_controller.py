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


class WindowController():
    """
    Controls tray, window creation, async update and deletion
    """

    def __init__(self, isserver=False, trayonly=False):
        self.istray = not isserver
        self.trayonly = trayonly
        self.isserver = isserver
        self.devices = {"vi": {}, "hi": {}, "a": {}, "b": {}}
        self.client = AudioClient(listen=True)
        self.config = self.client.config
        self.set_client_callbacks()
        if isserver: self.create_indicator()
        if not trayonly: self.create_window()
        Gtk.main()

    def create_device(self, device_type, device_id):
        device_config = self.config[device_type][device_id]
        name = device_config['name']
        mute = device_config['mute']
        volume = device_config['vol']
        primary, rnnoise, eq = None, None, None

        if name == '': return

        if device_type == 'vi':
            primary = device_config['primary']
            device = VirtualInput(name, mute, volume, primary)
            device.primary.connect('button_press_event', self.primary_click,
                    device_type, device_id)
            self.create_route_buttons(device, device_type, device_id)

        elif device_type == 'b':
            eq = device_config['use_eq']
            primary = device_config['primary']
            device = VirtualOutput(name, mute, volume, primary, eq)
            device.primary.connect('button_press_event', self.primary_click,
                    device_type, device_id)
            device.eq.connect('button_press_event', self.eq_click,
                    device_type, device_id)

        elif device_type == 'hi':
            rnnoise = device_config['use_rnnoise']
            device = HardwareInput(name, mute, volume, rnnoise)
            self.create_route_buttons(device, device_type, device_id)
            device.rnnoise.connect('button_press_event', self.rnnoise_click, device_id)

        elif device_type == 'a':
            eq = device_config['use_eq']
            name = device_config['nick']
            device = HardwareOutput(name, mute, volume, eq)
            device.eq.connect('button_press_event', self.eq_click,
                    device_type, device_id)

        device.volume.connect('value-changed', self.volume_change,
                device_type, device_id)
        device.mute.connect('button_press_event', self.mute_click,
                device_type, device_id)

        self.devices[device_type][device_id] = device
        self.main_window.create_device(device_type, device)

    def create_route_buttons(self, device, input_type, input_id):
        input_config = self.config[input_type][input_id]

        # iterate all outputs
        for output_type in ['a', 'b']:
            for output_id, output_config in self.config[output_type].items():
                key = 'nick' if output_type == 'a' else 'name'
                name = output_config[key]
                active = input_config[f'{output_type}{output_id}']['status']
                button = device.insert_output(output_type, output_id, name, active)

                button.connect('button_press_event', self.connect_click,
                        input_type, input_id, output_type, output_id)

    def volume_change(self, slider, device_type, device_id):
        device_config = self.config[device_type][device_id]
        val = int(slider.get_value())
        if device_config['vol'] != val:
            self.client.volume(device_type, device_id, val)

    def connect_click(self, button, event, input_type, input_id,
            output_type, output_id):

        if event.button == 1:
            state = not button.get_active()
            self.client.connect(input_type, input_id,
                    output_type, output_id, state)

        # right click
        elif event.button == 3:
            pass

    def mute_click(self, button, event):
        if not event.button == 1:
            return

        state = not self.mute.get_active()
        self.client.mute(self.device_type, self.device_id, state)

    def primary_click(self, button, event, device_type, device_id):
        if not event.button == 1:
            return

        button.set_sensitive(False)
        button.set_active(True)
        self.client.primary(device_type, device_id)

        for curr_id, device in self.devices[device_type].items():
            primary = device.primary
            if primary.get_active() and curr_id != device_id:
                primary.set_active(False)
                primary.set_state(False)
                primary.set_sensitive(True)

    def rnnoise_click(self, button, event, input_id):
        if event.button == 1:
            state = not button.get_active()
            self.client.rnnoise(input_id, state)

    def eq_click(self, button, event, output_type, output_id):
        if event.button == 1:
            state = not button.get_active()
            self.client.eq(output_type, output_id, state)

    def update_conect(self, input_type, input_id, output_type,
            output_id, state, latency=None):

        state = state == 'True'
        device = self.devices[input_type][input_id]
        button = device.route_dict[output_type][output_id]
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_mute(self, device_type, device_id, state):
        state = state == 'True'
        button = self.devices[device_type][device_id].mute
        curr_state = button.get_active()
        if state != curr_state:
            GLib.idle_add(button.set_active, state)

    def update_primary(self, device_type, device_id):
        for id, button in self.devices[device_type]:
            state = False if id != device_id else True
            GLib.idle_add(button.set_active, state)
            GLib.idle_add(button.set_sensitive, not state)

    def update_volume(self, device_type, device_id, value):
        value = int(value)
        slider = self.devices[device_type][device_id].volume
        curval = slider.get_value()
        if value != curval:
            GLib.idle_add(slider.set_value, value)

    def set_client_callbacks(self):
        cb = self.client.set_callback_function

        cb('exit', self.server_exit_event)
        cb('connect', self.update_conect)
        cb('mute', self.update_mute)
        cb('primary', self.update_primary)
        cb('volume', self.update_volume)

    def create_window(self):
        self.main_window = MainWindow(self.client)
        window = self.main_window.window
        window.connect('delete_event', self.delete_event)

        for device_type in ['vi', 'hi', 'a', 'b']:
            for device_id in self.config[device_type]:
                self.create_device(device_type, device_id)

        builder = self.main_window.builder
        builder.connect_signals(window)

        window.show_all()

    def delete_window(self):
        window = self.main_window.window
        if window is not None:
            window.destroy

    def create_indicator(self):
        indicator = AppIndicator3.Indicator.new(id='pulsemeetertray',
                icon_name='Pulsemeeter',
                category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

        state = self.client.config['tray']
        # state = True
        indicator.set_status(int(state))
        indicator.set_menu(self.tray_menu())
        self.indicator = indicator

    def tray_menu(self):
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
        try:
            self.main_window.window.present()
        except Exception:
            self.create_window()
            # self.windowinstance = self.start_window(self.isserver)
            # self.trayonly = False

    def toggle_indicator(self, state):
        if state:
            if self.indicator is None:
                self.create_indicator()
            self.indicator.set_status(1)
        else:
            self.indicator.set_status(0)

    def tray_exit(self, widget):
        self.delete_window()
        self.delete_event()

    def server_exit_event(self, widget=None, event=None):
        self.delete_window()
        Gtk.main_quit()

    def delete_event(self, widget=None, event=None):
        if self.isserver and self.indicator.get_status() == 0:
            self.client.close_server()
        else:
            self.client.stop_callbacks()
            self.client.stop_listen()

        Gtk.main_quit()
