import os
import time
import pulsectl
import re
import signal
import shutil
import threading
import sys
import json

from .app_list_widget import AppList
from .eq_popover import EqPopover
from .latency_popover import LatencyPopover
from .rnnoise_popover import RnnoisePopover
from .groups_popover import JackGroupsPopover
from .port_select_popover import PortSelectPopover
from .vumeter_widget import Vumeter

from ..settings import GLADEFILE, LAYOUT_DIR
from ..socket import Client

from gi import require_version as gi_require_version

# from pulsectl import Pulse
gi_require_version('Gtk', '3.0')
gi_require_version('AppIndicator3', '0.1')
from gi.repository import Gtk,Gdk,Gio,GLib,AppIndicator3

class MainWindow(Gtk.Window):

    def __init__(self, isserver=False, trayonly=False):

        self.isserver = isserver
        self.client = Client(listen=True)
        self.config = self.client.config
        self.trayonly = trayonly
        self.windowinstance = None
        self.tray = None

        if isserver:
            self.tray = self.create_indicator()
            self.client.set_callback_function('tray', self.update_tray_status)

        if trayonly: 
            self.client.set_callback_function('exit', self.close_on_server_exit)
            return

        self.windowinstance = self.start_window(isserver)
        # if self.config['tray'] and isserver:
            # self.create_indicator()

    def start_window(self, isserver):

        self.trayonly = False
        self.exit_flag = False
        GLib.threads_init()

        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        self.layout = self.config['layout']

        component_list = [
                    'window',
                    'menu_popover',
                    'rename_popover',
                    'popover_entry',
                    'latency_popover',
                    'latency_adjust',
                    'rnnoise_popover',
                    'rnnoise_latency_adjust',
                    'rnnoise_threshold_adjust',
                    'jack_group_popover',
                    'sink_input_list',
                    'source_output_list',
                    'sink_input_scroll',
                    'source_output_scroll',
                    'source_output_viewport',
                    'sink_input_viewport',
                    'vumeter_toggle',
                    'vi_1_peak',
                    'channel_groups',
                ]

        for i in range(1, 4):
            component_list.append(f'hi_{i}_adjust')
            component_list.append(f'vi_{i}_adjust')
            component_list.append(f'a_{i}_adjust')
            component_list.append(f'b_{i}_adjust')

                # os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
                component_list
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)


        self.devices = {}
        self.devices['a'] = self.client.list_hardware_devices('sinks')
        self.devices['hi'] = self.client.list_hardware_devices('sources')
        # self.devices['b'] = self.client.list_virtual_devices('sources')
        # self.devices['vi'] = self.client.list_virtual_devices('sinks')

        self.hardware_comboboxes = {}
        self.primary_buttons = {}
        self.volume_adjusts = {}
        self.volume_sliders = {}
        self.mute_buttons = {}
        self.loopback_buttons = {}
        self.rnnoise_buttons = {}
        self.eq_buttons = {}

        self.enable_vumeters = True
        if not shutil.which('pulse-vumeter') or self.config['enable_vumeters'] == False:
            self.enable_vumeters = False

        self.start_hardware_comboboxes()
        self.start_inputs()
        self.start_outputs()
        self.start_vumeters()
        self.start_app_list()
        self.start_menu_items()
        # self.start_layout_combobox()

        self.window = self.builder.get_object('window')
        # self.add_window(self.window)
        # super().__init__(self.window)

        self.listen_socket()

        self.window.connect('delete_event', self.delete_event)

        # self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)

        self.window.show_all()


        if not isserver:
            signal.signal(signal.SIGTERM, self.delete_event)
            signal.signal(signal.SIGINT, self.delete_event)

        return self.window

    def start_menu_items(self):
        if self.layout == 'default':
            self.menu_button = self.builder.get_object('menu_button')
            self.menu_popover = self.builder.get_object('menu_popover')
            self.menu_popover.set_relative_to(self.menu_button)

            self.menu_button.connect('pressed', self.open_settings)

        self.vumeter_toggle = self.builder.get_object('vumeter_toggle')
        self.vumeter_toggle.set_active(self.enable_vumeters)
        self.vumeter_toggle.connect('toggled', self.toggle_vumeters)

        self.cleanup_toggle = self.builder.get_object('cleanup_toggle')
        self.cleanup_toggle.set_active(self.config['cleanup'])
        self.cleanup_toggle.connect('toggled', self.toggle_cleanup)

        self.tray_toggle = self.builder.get_object('tray_toggle')
        self.tray_toggle.set_active(self.config['tray'])
        self.tray_toggle.connect('toggled', self.toggle_tray)

        self.layout_combobox = self.builder.get_object('layout_combobox')
        layout_list = os.listdir(LAYOUT_DIR)
        i = 0
        for layout in layout_list:
            self.layout_combobox.append_text(layout[:len(layout) - 6])
            if layout[:len(layout) - 6] == self.layout:
                self.layout_combobox.set_active(i)
            i += 1
        self.layout_combobox.connect('changed', self.change_layout)

        # self.jack_toggle_check_button = self.builder.get_object('jack_toggle')
        # self.jack_toggle_check_button.set_active(self.pulse.config['jack']['enable'])
        # self.jack_toggle_check_button.connect('toggled', self.toggle_jack)
        # self.jack_toggle_check_button.set_sensitive(False)


        # self.test = self.builder.get_object('test')
        # self.test.connect('pressed', self.open_group_popover)
        # self.jack_group_popover = self.builder.get_object('jack_group_popover')
        # self.jack_group_popover.set_relative_to(self.test)
        # self.jack_toggle_check_button.connect('toggled', self.toggle_jack)


    def toggle_tray(self, widget):
        state = widget.get_active()
        self.client.set_tray(state)
        if self.isserver:
            if state:
                if self.tray == None: self.tray = self.create_indicator()
                self.tray.set_status(1)
            else:
                self.tray.set_status(0)

    def toggle_cleanup(self, widget):
        self.client.set_cleanup(widget.get_active())

    # not perfect yet but works
    def change_layout(self, combobox):
        self.client.set_layout(combobox.get_active_text())
        self.windowinstance.destroy()
        self.windowinstance = self.start_window(self.isserver)
        self.trayonly = False
        # self.delete_event()

    def open_settings(self, widget):
        self.menu_popover.popup()

    def toggle_jack(self, widget):
        self.pulse.config['jack']['enable'] = widget.get_active()
        for i in ['vi', 'hi']:
            for j in self.pulse.config[i]:
                self.pulse.config[i][j]['jack'] = widget.get_active()

    def toggle_vumeters(self, widget):
        if not shutil.which('pulse-vumeter'):
            return
        self.enable_vumeters = widget.get_active()
        self.config['enable_vumeters'] = widget.get_active()
        for device_type in ['hi', 'vi', 'a', 'b']:
            for device_id in self.config[device_type]:
                # if self.config[device_type][device_id]['name'] != '':
                if widget.get_active() == False:
                    self.vu_list[device_type][device_id].close()
                else:
                    self.vu_list[device_type][device_id].reload_device()
                    self.vu_list[device_type][device_id].start()

    def start_vumeters(self):
        self.vu_list = {}
        for device_type in ['hi', 'vi', 'a', 'b']:
            self.vu_list[device_type] = {}
            for device_id in self.config[device_type]:
                device_config = self.config[device_type][device_id]
                grid = self.builder.get_object(f'{device_type}_{device_id}_vumeter')
                vert = True if self.layout == 'default' else False
                vumeter = Vumeter(device_type, device_id, self.config, vertical=vert)
                grid.add(vumeter)
                if device_config['name'] != '':
                    if self.enable_vumeters == True:
                        try:
                            vumeter.start() 
                        except:
                            print(f'Could not start vumeter for {device_type}{device_id}')
                           
                self.vu_list[device_type][device_id] = vumeter

    def start_app_list(self):
        # this is probably not the best solution but it handles the pactl errors fine
        sink_input_viewport = self.builder.get_object('sink_input_viewport')
        source_output_viewport = self.builder.get_object('source_output_viewport')
        try:
            self.sink_input_box = AppList('sink-input', self.client)
            self.source_output_box = AppList('source-output', self.client)

            sink_input_viewport.add(self.sink_input_box)
            source_output_viewport.add(self.source_output_box)

            self.subscribe_thread = threading.Thread(target=self.listen_subscribe, args=())
            self.subscribe_thread.start()
        except Exception as ex:
            print('App sinks returned an error, audio backend probably crashed. Server will be closed.')
            if self.windowinstance is not None:
                self.windowinstance.destroy()
            self.delete_event()
            try:
                # I need to create a new client so it stops listening
                client = Client()
                client.close_server()
            except:
                print('Could not close server.')
            sys.exit(1)


    def start_hardware_comboboxes(self):
        for device_type in ['hi', 'a']:
            self.hardware_comboboxes[device_type] = {}
            name_size = 35 if device_type == 'a' else 20
            if self.layout != 'default':
                name_size = 100
            devices = self.devices[device_type]

            # for each combobox
            found = False
            for device_id in self.config[device_type]:
                device_config = self.config[device_type][device_id]
                combobox = self.builder.get_object(f'{device_type}_{device_id}_combobox')
                combobox.append_text('')

                for i in range(0, len(devices)):
                    text = devices[i]['description'][:name_size]
                    if len(text) == name_size:
                        text = text + '...'
                    combobox.append_text(text)
                    if devices[i]['name'] == device_config['name']:
                        found = True
                        combobox.set_active(i + 1)

                if found == False and device_config['jack'] == False:
                    device_config['name'] = ''

                combobox.connect('changed', self.on_combo_changed, device_type, device_id, devices)
                self.hardware_comboboxes[device_type][device_id] = combobox

    def start_inputs(self):
        self.rename_popover = self.builder.get_object('rename_popover')
        self.Popover_Entry = self.builder.get_object('popover_entry')
        self.Popover_Entry.connect('activate', self.label_rename_entry)

        self.primary_buttons['vi'] = {}

        # for each input device
        for input_type in ['hi', 'vi']:

            self.volume_adjusts[input_type] = {}
            self.volume_sliders[input_type] = {}
            self.mute_buttons[input_type] = {}
            self.loopback_buttons[input_type] = {}

            for input_id in self.config[input_type]:

                if input_type == 'vi':
                    name = self.config['vi'][input_id]['name']
                    label = self.builder.get_object(f'vi_{input_id}_label')
                    label.set_text(name if name != '' else f'Virtual Input {input_id}')
                    label_evt_box = self.builder.get_object(
                            f'vi_{input_id}_label_event_box')
                    label_evt_box.connect('button_press_event', self.label_click, label,
                            'vi', input_id)
                    primary = self.builder.get_object(f'vi_{input_id}_primary')
                    primary.set_active(self.config['vi'][input_id]['primary'])
                    if self.config['vi'][input_id]['primary'] == True:
                        primary.set_sensitive(False)
                    primary.connect('clicked', self.toggle_primary, 'vi', input_id)
                    self.primary_buttons['vi'][input_id] = primary

                else:

                    # noise reduction button
                    rnnoise = self.builder.get_object(f'hi_{input_id}_rnnoise')
                    rnnoise.set_active(self.config['hi'][input_id]['use_rnnoise'])
                    rnnoise.connect('clicked', self.toggle_rnnoise, 'hi', input_id)

                    rnnoise.connect('button_press_event', self.open_popover, 
                            RnnoisePopover, input_type, input_id)
                    self.rnnoise_buttons[input_id] = rnnoise
                    # check for rnnoise plugin
                    found = 0
                    for lib in ['lib', 'lib64']:
                        for path in [f'/usr/{lib}/ladspa', f'/usr/local/{lib}/ladspa']:
                            if os.path.isfile(os.path.join(path, 
                                'librnnoise_ladspa.so')): 
                                found = 1
                                break
                            elif os.path.isfile(os.path.join(path, 
                                'rnnoise_ladspa.so')):
                                found = 1
                                break
                    if found == 0:
                        rnnoise.set_visible(False)
                        rnnoise.set_no_show_all(True)


                # recover volume if possible
                source_config = self.config[input_type][input_id]
                # for source in self.devices[input_type]:
                    # if source['name'] == source_config['name'] and 'volume' in source:
                        # source_config['vol'] = source['volume']

                # connect volume sliders
                adjust = self.builder.get_object(f'{input_type}_{input_id}_adjust')
                adjust.set_value(source_config['vol'])
                vol_slider = self.builder.get_object(f'{input_type}_{input_id}_vol')
                vol_slider.connect('value-changed', self.volume_change, 
                        input_type, input_id)
                vol_slider.add_mark(100, Gtk.PositionType.TOP, '')
                self.volume_adjusts[input_type][input_id] = adjust
                self.volume_sliders[input_type][input_id] = vol_slider

                # connect mute buttons
                mute = self.builder.get_object(f'{input_type}_{input_id}_mute')
                mute.set_active(self.config[input_type][input_id]['mute'])
                mute.connect('clicked', self.toggle_mute, input_type, input_id)
                self.mute_buttons[input_type][input_id] = mute

                # connection buttons
                self.loopback_buttons[input_type][input_id] = {}
                for output_type in ['a', 'b']:
                    for output_id in self.config[output_type]:
                        sink = output_type + output_id
                        button = self.builder.get_object(f'{input_type}_{input_id}_{sink}')
                        button.set_active(source_config[sink])
                        self.loopback_buttons[input_type][input_id][sink] = button
                        button.connect('clicked', self.toggle_loopback, input_type,
                                input_id, output_type, output_id)

                        if self.config['jack']['enable'] == False:
                            button.connect('button_press_event', self.latency_popover, LatencyPopover,
                                    input_type, input_id, output_type, output_id)
                        else:
                            button.connect('button_press_event', self.open_popover, PortSelectPopover, 
                                    [input_type, input_id, sink])

    # start output devices
    def start_outputs(self):

        self.primary_buttons['b'] = {}

        for output_type in ['a', 'b']:

            self.volume_adjusts[output_type] = {}
            self.volume_sliders[output_type] = {}
            self.mute_buttons[output_type] = {}
            self.eq_buttons[output_type] = {}

            for output_id in self.config[output_type]:

                sink_config = self.config[output_type][output_id]

                if output_type == 'b':
                    primary = self.builder.get_object(f'b_{output_id}_primary')
                    primary.set_active(sink_config['primary'])
                    if sink_config['primary'] == True:
                        primary.set_sensitive(False)

                    primary.connect('clicked', self.toggle_primary, 'b', output_id)
                    self.primary_buttons['b'][output_id] = primary

                    label = self.builder.get_object(f'b{output_id}_label')
                    if label != None:
                        label.set_text(f'B{output_id} - {sink_config["name"]}')

                # for sink in self.devices[output_type]:
                    # if sink['name'] == sink_config['name'] and 'volume' in sink:
                        # sink_config['vol'] = sink['volume']
                
                # volume slider and adjustment 
                adjust = self.builder.get_object(f'{output_type}_{output_id}_adjust')
                adjust.set_value(sink_config['vol'])
                vol_slider = self.builder.get_object(f'{output_type}_{output_id}_vol')
                vol_slider.connect('value-changed', self.volume_change, output_type, 
                        output_id)
                vol_slider.add_mark(100, Gtk.PositionType.TOP, '')
                self.volume_adjusts[output_type][output_id] = adjust
                self.volume_sliders[output_type][output_id] = vol_slider

                # mute button
                mute = self.builder.get_object(f'{output_type}_{output_id}_mute')
                mute.set_active(sink_config['mute'])
                mute.connect('clicked', self.toggle_mute, output_type, output_id)
                self.mute_buttons[output_type][output_id] = mute

                # eq button
                eq = self.builder.get_object(f'{output_type}_{output_id}_eq')
                eq.set_active(sink_config['use_eq'])
                eq.connect('clicked', self.toggle_eq, output_type, output_id)
                eq.connect('button_press_event', self.open_popover, EqPopover, 
                        output_type, output_id)
                self.eq_buttons[output_type][output_id] = eq

                # to hide eq button if plugin not found
                found = 0
                for arc in ['', '64']:
                    for path in [f'/usr/lib{arc}/ladspa', 
                            f'/usr/local/lib{arc}/ladspa']:
                        if os.path.isfile(os.path.join(path, 'mbeq_1197.so')):
                            found = 1
                    if found == 0:
                        eq.set_visible(False)
                        eq.set_no_show_all(True)

    def toggle_eq(self, button, output_type, output_id):
        state = button.get_active()
        self.client.eq(output_type, output_id, state)

    def toggle_rnnoise(self, widget, input_type, input_id):
        state = widget.get_active()
        self.client.rnnoise(input_id, state)

    def toggle_mute(self, button, device_type, device_id):
        state = button.get_active()
        self.client.mute(device_type, device_id, state)

    def toggle_loopback(self, button, input_type, input_id, output_type, output_id):
        state = button.get_active()
        self.client.connect(input_type, input_id, output_type, output_id, state)

    def volume_change(self, slider, device_type, device_id):
        val = int(slider.get_value())
        if self.config[device_type][device_id]['vol'] != val:
            self.client.volume(device_type, device_id, val)

    def open_group_popover(self, widget):
        JackGroupsPopover(widget, self.pulse)

    def open_popover(self, button, event, popover, device_type, device_id):
        if event.button == 3:
            if self.config[device_type][device_id]['name'] != '':
                popover(button, self.client, device_type, device_id)

    def latency_popover(self, button, event, popover, input_type, input_id, 
            output_type, output_id):
        if event.button == 3:
            if self.config[input_type][input_id]['name'] != '':
                popover(button, self.client, [input_type, input_id], 
                        [output_type, output_id])

    def label_rename_entry(self, widget):
        name = widget.get_text()
        device_type = self.rename_device_type
        device_id = self.rename_device_id
        old_name = self.active_label.get_text()
        if re.match('^[a-zA-Z0-9"_"]*$', name) and name != old_name:
            self.client.rename(device_type, device_id, name)
            self.active_label.set_text(name)
            # self.sink_input_box.load_application_list()
            # self.source_output_box.load_application_list()
            self.vu_list[device_type][device_id].restart()
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.windowinstance,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text='name is not allowed'
            )
            dialog.format_secondary_text('The name can only consist of numbers, letters and "_".')
            dialog.run()
            dialog.destroy()
            return

        self.rename_popover.popdown()

    def label_click(self, widget, event, label, device_type, device_id):
        self.rename_device_type = device_type
        self.rename_device_id = device_id
        self.active_label = label
        self.rename_popover.set_relative_to(widget)
        self.rename_popover.popup()

    def on_combo_changed(self, widget, output_type, output_id, device):
        model = widget.get_active()
        name = device[model - 1]['name'] if model > 0 else ''

        self.client.change_hardware_device(output_type, output_id, name)
        self.vu_list[output_type][output_id].restart()

        # if re.search('JACK:', device[model - 1]['description']):
            # self.pulse.config[device_type][device_id]['jack'] = True
        # else:
            # self.pulse.config[device_type][device_id]['jack'] = False

    def toggle_primary(self, widget, device_type, device_id):
        if widget.get_active() == False:
            return
        else:
            widget.set_sensitive(False)
            button_list = self.primary_buttons[device_type]
            for button in button_list:
                if button_list[button] != widget:
                    button_list[button].set_sensitive(True)
                    button_list[button].set_active(False)

        self.client.primary(device_type, device_id)
        # if index[0] == 'vi':
            # self.sink_input_box.load_application_list()
        # else:
            # self.source_output_box.load_application_list()

    def listen_subscribe(self):
        for i in self.client.subscribe():

            if 'remove' in i:
                id = i.split('#')[1].strip('\n')
                if 'sink-input' in i:
                    GLib.idle_add(self.sink_input_box.remove_app_dev, id)

                elif 'source-output' in i:
                    GLib.idle_add(self.source_output_box.remove_app_dev, id)

            elif 'new' in i:
                id = i.split('#')[1].strip('\n')
                if 'sink-input' in i:
                    GLib.idle_add(self.sink_input_box.load_application_list, id)

                elif 'source-output' in i:
                    GLib.idle_add(self.source_output_box.load_application_list, id)


    def listen_socket(self):
        self.client.set_callback_function('connect', 
                self.update_loopback_buttons)
        self.client.set_callback_function('mute', 
                self.update_mute_buttons)
        self.client.set_callback_function('primary', 
                self.update_primary_buttons)
        self.client.set_callback_function('rnnoise', 
                self.update_rnnoise_buttons)
        self.client.set_callback_function('eq', 
                self.update_eq_buttons)
        self.client.set_callback_function('volume', 
                self.update_volume_slider)
        self.client.set_callback_function('change-hd', 
                self.update_comboboxes)

        self.client.set_callback_function('exit', 
                self.close_on_server_exit)


    def close_on_server_exit(self):
        if not self.trayonly:
            self.client.end_subscribe()
            self.subscribe_thread.join()
            if self.enable_vumeters == True:
                for i in ['hi', 'vi', 'a', 'b']:
                    for j in self.vu_list[i]:
                        self.vu_list[i][j].close()
            GLib.idle_add(self.window.destroy)
        Gtk.main_quit()

    def update_loopback_buttons(self, input_type, input_id, output_type,
            output_id, state, latency):

        sink = output_type + output_id
        state = state == 'True'
        
        button = self.loopback_buttons[input_type][input_id][sink]
        
        GLib.idle_add(button.set_active, state)

    def update_mute_buttons(self, input_type, input_id, state):
        state = state == 'True'
        
        button = self.mute_buttons[input_type][input_id]
        GLib.idle_add(button.set_active, state)

    def update_volume_slider(self, device_type, device_id, val):
        val = int(val)
        
        adjust = self.volume_adjusts[device_type][device_id]
        GLib.idle_add(adjust.set_value, val)

    def update_primary_buttons(self, device_type, device_id):
        
        button_list = self.primary_buttons[device_type]
        for dev_id in button_list:
            if dev_id == device_id:
                GLib.idle_add(button_list[dev_id].set_active, True)
                GLib.idle_add(button_list[dev_id].set_sensitive, False)
            else:
                GLib.idle_add(button_list[dev_id].set_active, False)
                GLib.idle_add(button_list[dev_id].set_sensitive, True)
        
    def update_rnnoise_buttons(self, input_id, state, control):
        state = state == 'True'
        
        button = self.rnnoise_buttons[input_id]
        GLib.idle_add(button.set_active, state)

    def update_eq_buttons(self, output_type, output_id, state, control):
        state = state == 'True'
        
        button = self.eq_buttons[output_type][output_id]
        GLib.idle_add(button.set_active, state)

    def update_comboboxes(self, device_type, device_id, device):
        if device == 'None': device = ''
        devices = self.devices[device_type]

        # for each combobox
        device_config = self.config[device_type][device_id]
        combobox = self.hardware_comboboxes[device_type][device_id]

        found = False
        for i in range(0, len(devices)):
            if devices[i]['name'] == device:
                found = True
                combobox.set_active(i + 1)

        if found == False and device_config['jack'] == False:
            combobox.set_active(0)

    def update_tray_status(self, state):
        if type(state) == str:
            state = state.lower() == 'true'

        if not self.trayonly:
            GLib.idle_add(self.tray_toggle.set_active, state)

        if self.isserver:
            GLib.idle_add(self.tray.set_status, int(state))


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

    def create_indicator(self):
        indicator = AppIndicator3.Indicator.new(id='pulsemeetertray',
                icon_name='Pulsemeeter',
                category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

        indicator.set_status(int(self.config['tray']))

        indicator.set_menu(self.tray_menu())
        return indicator
        # Gtk.main()

    def open_ui(self, widget):
        #os.popen('pulsemeeter')
        try:
            self.windowinstance.present()
        except:
            self.windowinstance = self.start_window(self.isserver)
            self.trayonly = False


    def tray_exit(self, widget):
        if self.windowinstance != None:
            self.windowinstance.close()
        self.delete_event()
        # maybe TODO: the self.client does not stop listening even with stop listen
        # client = Client()
        # client.close_server()

        Gtk.main_quit()
        return 0

    def delete_event(self, widget=None, event=None):
        if not self.trayonly:
            self.client.end_subscribe()
            try:
                self.subscribe_thread.join()
            except:
                # when the application didnt manage to start the app list there is no thread.
                print('Could not join subscribe_thread (maybe there is none)')
            if self.enable_vumeters == True:
                for i in ['hi', 'vi', 'a', 'b']:
                    for j in self.vu_list[i]:
                        self.vu_list[i][j].close()
            self.trayonly = True
            self.windowinstance = None

        if not self.config['tray'] or not self.isserver:
            self.client.close_connection()
            self.client.stop_listen()
            Gtk.main_quit()

        return False
