import os
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

from ..settings import GLADEFILE, LAYOUT_DIR

from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk,Gio,GLib

class MainWindow(Gtk.Window):

    def __init__(self, sock):

        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        self.sock = sock
        init_config = sock.send_command('get-config')
        self.init_config = json.loads(init_config)
        # self.pulse = pulse
        # self.pulse.restart_window = False
        self.layout = self.init_config['layout']

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
        self.devices['a'] = json.loads(self.sock.send_command('get-hd sinks'))
        self.devices['b'] = json.loads(self.sock.send_command('get-vd sources'))
        self.devices['vi'] = json.loads(self.sock.send_command('get-vd sinks'))
        self.devices['hi'] = json.loads(self.sock.send_command('get-hd sources'))

        self.hardware_comboboxes = {}
        self.primary_buttons = {}
        self.volume_adjusts = {}
        self.volume_sliders = {}
        self.mute_buttons = {}
        self.loopback_buttons = {}
        self.rnnoise_buttons = {}
        self.eq_buttons = {}

        # if not 'enable_vumeters' in self.pulse.config:
            # self.pulse.config['enable_vumeters'] = True

        # self.enable_vumeters = True
        # if not shutil.which('pulse-vumeter') or self.pulse.config['enable_vumeters'] == False:
            # self.enable_vumeters = False

        # self.vumeter_toggle = self.builder.get_object('vumeter_toggle')
        # self.vumeter_toggle.set_active(self.enable_vumeters)
        # self.vumeter_toggle.connect('toggled', self.toggle_vumeters)
        # self.jack_toggle_check_button = self.builder.get_object('jack_toggle')
        # self.jack_toggle_check_button.set_active(self.pulse.config['jack']['enable'])
        # self.jack_toggle_check_button.connect('toggled', self.toggle_jack)
        # self.jack_toggle_check_button.set_sensitive(False)


        # self.test = self.builder.get_object('test')
        # self.test.connect('pressed', self.open_group_popover)
        # self.jack_group_popover = self.builder.get_object('jack_group_popover')
        # self.jack_group_popover.set_relative_to(self.test)



        # self.jack_toggle_check_button.connect('toggled', self.toggle_jack)
        self.start_hardware_comboboxes()
        self.start_inputs()
        self.start_outputs()
        # self.start_app_list()
        # self.start_vumeters()
        # self.start_layout_combobox()

        self.window = self.builder.get_object('window')
        super().__init__(self.window)

        # if self.layout == 'default':
            # self.menu_button = self.builder.get_object('menu_button')
            # self.menu_popover = self.builder.get_object('menu_popover')
            # self.menu_popover.set_relative_to(self.menu_button)

            # self.menu_button.connect('pressed', self.open_settings)

        self.window.connect('delete_event', self.delete_event)

        # self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)

        self.window.show_all()

        signal.signal(signal.SIGTERM, self.delete_event)
        signal.signal(signal.SIGINT, self.delete_event)

        # self.subscribe_thread.start()

    def start_layout_combobox(self):
        self.layout_combobox = self.builder.get_object('layout_combobox')
        layout_list = os.listdir(LAYOUT_DIR)
        i = 0
        for layout in layout_list:
            self.layout_combobox.append_text(layout[:len(layout) - 6])
            if layout[:len(layout) - 6] == self.layout:
                self.layout_combobox.set_active(i)
            i += 1
        self.layout_combobox.connect('changed', self.change_layout)

    def change_layout(self, combobox):
        self.pulse.config['layout'] = combobox.get_active_text()
        self.pulse.restart_window = True
        self.window.destroy()
        self.delete_event(None, None)

    def open_settings(self, widget):
        self.menu_popover.popup()

    def toggle_jack(self, widget):
        self.pulse.config['jack']['enable'] = widget.get_active()
        for i in ['vi', 'hi']:
            for j in self.pulse.config[i]:
                self.pulse.config[i][j]['jack'] = widget.get_active()
        # if widget.get_active() == True:
            # pass
            

    def toggle_vumeters(self, widget):
        if not shutil.which('pulse-vumeter'):
            return
        self.enable_vumeters = widget.get_active()
        self.pulse.config['enable_vumeters'] = widget.get_active()
        if widget.get_active() == False:
            self.pulse.end_vumeter()
        for i in ['hi', 'vi', 'a', 'b']:
            for j in ['1','2','3']:
                if self.pulse.config[i][j]['name'] != '':
                    if widget.get_active() == False:
                        self.vu_list[i][j].set_fraction(0)
                        self.vu_thread[i][j].join() 
                    else:
                        self.vu_thread[i][j] = threading.Thread(target=self.listen_peak, 
                                args=([i, j],))
                        self.vu_thread[i][j].start() 

    def start_vumeters(self):
        self.vu_list = {}
        self.vu_thread = {}
        for i in ['hi', 'vi', 'a', 'b']:
            self.vu_list[i] = {}
            self.vu_thread[i] = {}
            for j in ['1','2','3']:
                grid = self.builder.get_object(f'{i}_{j}_vumeter')
                self.vu_list[i][j] = Gtk.ProgressBar()
                if self.layout == 'default':
                    self.vu_list[i][j].set_orientation(Gtk.Orientation.VERTICAL)
                    self.vu_list[i][j].set_margin_bottom(8)
                    self.vu_list[i][j].set_margin_top(8)
                    self.vu_list[i][j].set_halign(Gtk.Align.CENTER)
                    self.vu_list[i][j].set_inverted(True)
                else:
                    self.vu_list[i][j].set_orientation(Gtk.Orientation.HORIZONTAL)
                self.vu_list[i][j].set_vexpand(True)
                self.vu_list[i][j].set_hexpand(True)

                grid.add(self.vu_list[i][j])
                if self.pulse.config[i][j]['name'] != '':
                    self.vu_thread[i][j] = threading.Thread(target=self.listen_peak, 
                            args=([i, j],))
                    if self.enable_vumeters == True:
                        self.vu_thread[i][j].start() 

    def restart_vumeter(self, index, stop=True, start=True):
        if self.enable_vumeters == False:
            return
        if stop:
            if index[1] in self.pulse.vu_list[index[0]] or stop_only == True:
                if index[1] in self.vu_thread[index[0]]:
                    self.pulse.vu_list[index[0]][index[1]].terminate()
                    # self.pulse.vu_list[index[0]].pop(index[1])
                    self.vu_thread[index[0]][index[1]].join()
                    self.vu_thread[index[0]].pop(index[1])
                self.vu_list[index[0]][index[1]].set_fraction(0)

        if not start:
            return

        self.vu_thread[index[0]][index[1]] = threading.Thread(target=self.listen_peak, 
                args=(index,))
        self.vu_thread[index[0]][index[1]].start()


    def start_app_list(self):
        sink_input_viewport = self.builder.get_object('sink_input_viewport')
        source_output_viewport = self.builder.get_object('source_output_viewport')
        self.sink_input_box = AppList('sink-input', self.pulse)
        self.source_output_box = AppList('source-output', self.pulse)
        sink_input_viewport.add(self.sink_input_box)
        source_output_viewport.add(self.source_output_box)

        self.subscribe_thread = threading.Thread(target=self.listen_subscribe, args=())

    def start_hardware_comboboxes(self):
        for device_type in ['hi', 'a']:
            self.hardware_comboboxes[device_type] = {}
            name_size = 35 if device_type == 'a' else 20
            if self.layout != 'default':
                name_size = 100
            devices = self.devices[device_type]

            # for each combobox
            found = False
            for device_num in self.init_config[device_type]:
                device_config = self.init_config[device_type][device_num]
                combobox = self.builder.get_object(f'{device_type}_{device_num}_combobox')
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

                combobox.connect('changed', self.on_combo_changed, device_type, device_num, devices)
                self.hardware_comboboxes[device_type][device_num] = combobox

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

            for input_id in self.init_config[input_type]:

                if input_type == 'vi':
                    name = self.init_config['vi'][input_id]['name']
                    label = self.builder.get_object(f'vi_{input_id}_label')
                    label.set_text(name if name != '' else f'Virtual Input {input_id}')
                    label_evt_box = self.builder.get_object(f'vi_{input_id}_label_event_box')
                    label_evt_box.connect('button_press_event', self.label_click, label, 'vi', input_id)
                    primary = self.builder.get_object(f'vi_{input_id}_primary')
                    primary.set_active(self.init_config['vi'][input_id]['primary'])
                    if self.init_config['vi'][input_id]['primary'] == True:
                        primary.set_sensitive(False)
                    primary.connect('clicked', self.toggle_primary, 'vi', input_id)
                    self.primary_buttons['vi'][input_id] = primary

                else:

                    # noise reduction button
                    rnnoise = self.builder.get_object(f'hi_{input_id}_rnnoise')
                    rnnoise.set_active(self.init_config['hi'][input_id]['use_rnnoise'])
                    rnnoise.connect('clicked', self.toggle_rnnoise, 'hi', input_id)
                    self.rnnoise_buttons[input_id] = rnnoise
                    # check for rnnoise plugin
                    found = 0
                    for arc in ['', '64']:
                        for path in [f'/usr/lib{arc}/ladspa', f'/usr/local/lib{arc}/ladspa']:
                            if os.path.isfile(os.path.join(path, 'librnnoise_ladspa.so')): 
                                found = 1
                                break
                            elif os.path.isfile(os.path.join(path, 'rnnoise_ladspa.so')):
                                found = 1
                                break
                    if found == 0:
                        rnnoise.set_visible(False)
                        rnnoise.set_no_show_all(True)


                # recover volume if possible
                source_config = self.init_config[input_type][input_id]
                for source in self.devices[input_type]:
                    if source['name'] == source_config['name'] and 'volume' in source:
                        source_config['vol'] = source['volume']

                # connect volume sliders
                adjust = self.builder.get_object(f'{input_type}_{input_id}_adjust')
                adjust.set_value(source_config['vol'])
                vol_slider = self.builder.get_object(f'{input_type}_{input_id}_vol')
                vol_slider.connect('value-changed', self.volume_change, input_type, input_id)
                vol_slider.add_mark(100, Gtk.PositionType.TOP, '')
                self.volume_adjusts[input_type][input_id] = adjust
                self.volume_sliders[input_type][input_id] = vol_slider

                # connect mute buttons
                mute = self.builder.get_object(f'{input_type}_{input_id}_mute')
                mute.set_active(self.init_config[input_type][input_id]['mute'])
                mute.connect('clicked', self.toggle_mute, input_type, input_id)
                self.mute_buttons[input_type][input_id] = mute

                # connection buttons
                self.loopback_buttons[input_type] = {}
                self.loopback_buttons[input_type][input_id] = {}
                for output_type in ['a', 'b']:
                    for output_id in self.init_config[output_type]:
                        sink = output_type + output_id
                        button = self.builder.get_object(f'{input_type}_{input_id}_{sink}')
                        button.set_active(source_config[sink])
                        self.loopback_buttons[input_type][input_id][sink] = button
                        button.connect('clicked', self.toggle_loopback, input_type,
                                input_id, output_type, output_id)

                        # if self.init_config['jack']['enable'] == False:
                            # button.connect('button_press_event', self.open_popover, LatencyPopover,
                                    # [input_type, input_id, sink])
                        # else:
                            # button.connect('button_press_event', self.open_popover, PortSelectPopover, 
                                    # [input_type, input_id, sink])

    # start output devices
    def start_outputs(self):

        self.primary_buttons['b'] = {}

        for output_type in ['a', 'b']:

            self.volume_adjusts[output_type] = {}
            self.volume_sliders[output_type] = {}
            self.mute_buttons[output_type] = {}

            for output_id in self.init_config[output_type]:

                sink_config = self.init_config[output_type][output_id]

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

                for sink in self.devices[output_type]:
                    if sink['name'] == sink_config['name'] and 'volume' in sink:
                        sink_config['vol'] = sink['volume']
                
                # volume slider and adjustment 
                adjust = self.builder.get_object(f'{output_type}_{output_id}_adjust')
                adjust.set_value(sink_config['vol'])
                vol_slider = self.builder.get_object(f'{output_type}_{output_id}_vol')
                vol_slider.connect('value-changed', self.volume_change, output_type, output_id)
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
                # eq.connect('button_press_event', self.open_popover, EqPopover, [output_type, output_id])

                # to hide eq button if plugin not found
                found = 0
                for arc in ['', '64']:
                    for path in [f'/usr/lib{arc}/ladspa', f'/usr/local/lib{arc}/ladspa']:
                        if os.path.isfile(os.path.join(path, 'mbeq_1197.so')):
                            found = 1
                    if found == 0:
                        eq.set_visible(False)
                        eq.set_no_show_all(True)

    def toggle_eq(self, button, output_type, output_id):
        state = button.get_active()
        self.sock.send_command(f'eq {output_type} {output_id} {state}')

    def toggle_rnnoise(self, widget, input_type, input_id):
        state = widget.get_active()
        self.sock.send_command(f'rnnoise {input_id} {state}')

    def toggle_mute(self, button, device_type, device_num):
        state = 1 if button.get_active() else 0
        self.sock.send_command(f'mute {device_type} {device_num} {state}')

    def toggle_loopback(self, button, input_type, input_id, output_type, output_id):
        state =  button.get_active()
        self.sock.send_command(f'connect {input_type} {input_id} {output_type} {output_id} {state}')

    def volume_change(self, slider, device_type, device_num):
        val = int(slider.get_value())
        self.sock.send_command(f'volume {device_type} {device_num} {val}')

    # def open_group_popover(self, widget):
        # JackGroupsPopover(widget, self.pulse)

    def open_popover(self, button, event, popover, index):
        if event.button == 3:
            if self.pulse.config[index[0]][index[1]]['name'] != '':
                popover(button, self.pulse, index)

    def label_rename_entry(self, widget):
        name = widget.get_text()
        old_name = self.active_label.get_text()
        if re.match('^[a-zA-Z0-9]*$', name) and name != old_name:
            self.sock.send_command(f'rename {self.rename_device_type} {self.rename_device_id} {name}')
            self.active_label.set_text(name)
            self.sink_input_box.load_application_list()
            self.source_output_box.load_application_list()
            # self.restart_vumeter(self.Label_Index)

        else:
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
        print(name)

        self.sock.send_command(f'change_hd {output_type} {output_id} {name}')
        # start = True if model > 0 else False
        # self.restart_vumeter([output_type, output_id], stop=True, start=start)

        # if re.search('JACK:', device[model - 1]['description']):
            # self.pulse.config[device_type][device_num]['jack'] = True
        # else:
            # self.pulse.config[device_type][device_num]['jack'] = False

    def toggle_primary(self, widget, device_type, device_num):
        if widget.get_active() == False:
            return
        else:
            widget.set_sensitive(False)
            button_list = self.primary_buttons[device_type]
            for button in button_list:
                if button_list[button] != widget:
                    button_list[button].set_sensitive(True)
                    button_list[button].set_active(False)

        self.sock.send_command(f'primary {device_type} {device_num}')
        # if index[0] == 'vi':
            # self.sink_input_box.load_application_list()
        # else:
            # self.source_output_box.load_application_list()


    def listen_subscribe(self):
        for i in self.pulse.subscribe():

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

    def listen_peak(self, index):
        old = 0
        for i in self.pulse.vumeter(index):
            try:
                val = float(i.strip('\n'))
                GLib.idle_add(self.vu_list[index[0]][index[1]].set_fraction, val)
            except:
                return

    def delete_event(self, widget, event):
        # self.pulse.save_config()
        # self.pulse.end_subscribe()
        # self.subscribe_thread.join()
        # if self.enable_vumeters == True:
            # self.pulse.end_vumeter()
            # for i in ['hi', 'vi', 'a', 'b']:
                # for j in ['1','2','3']:
                    # if j in self.vu_thread[i]:
                        # self.vu_thread[i][j].join()
        Gtk.main_quit()
        return False
