import os
import signal
import shutil
import threading
import sys
import json

from .EqPopover import EqPopover
from .RnnoisePopover import RnnoisePopover
from .LatencyPopover import LatencyPopover
from .AppListWidget import AppList
from .settings import GLADEFILE

from gi.repository import Gtk,Gdk,Gio,GLib

class MainWindow(Gtk.Window):

    def __init__(self, pulse):

        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        self.pulse = pulse

        component_list = [
                    'window',
                    'menu_button',
                    'menu_popover',
                    'rename_popover',
                    'popover_entry',
                    'latency_popover',
                    'latency_adjust',
                    'rnnoise_popover',
                    'rnnoise_latency_adjust',
                    'rnnoise_threshold_adjust',
                    'sink_input_list',
                    'source_output_list',
                    'sink_input_scroll',
                    'source_output_scroll',
                    'source_output_viewport',
                    'sink_input_viewport',
                    'vumeter_toggle',
                    'vi_1_peak',
                ]

        for i in range(1, 4):
            component_list.append(f'hi_{i}_adjust')
            component_list.append(f'vi_{i}_adjust')
            component_list.append(f'a_{i}_adjust')
            component_list.append(f'b_{i}_adjust')

        try:
            self.builder.add_objects_from_file(
                GLADEFILE,
                component_list
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)
        if not 'enable_vumeters' in self.pulse.config:
            self.pulse.config['enable_vumeters'] = True

        self.enable_vumeters = True
        if not shutil.which('pulse-vumeter') or self.pulse.config['enable_vumeters'] == False:
            self.enable_vumeters = False

        self.vumeter_toggle = self.builder.get_object('vumeter_toggle')
        self.vumeter_toggle.set_active(self.enable_vumeters)
        self.vumeter_toggle.connect('toggled', self.toggle_vumeters)
        self.start_hardware_comboboxes()
        self.start_inputs()
        self.start_outputs()
        self.start_app_list()
        self.start_vumeters()

        self.window = self.builder.get_object('window')
        super().__init__(self.window)

        self.menu_button = self.builder.get_object('menu_button')
        self.menu_popover = self.builder.get_object('menu_popover')
        self.menu_popover.set_relative_to(self.menu_button)

        self.menu_button.connect('pressed', self.open_settings)

        self.window.connect('delete_event', self.delete_event)

        self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)

        self.window.show_all()

        signal.signal(signal.SIGTERM, self.delete_event)
        signal.signal(signal.SIGINT, self.delete_event)

        self.subscribe_thread.start()

    def open_settings(self, widget):
        self.menu_popover.popup()

    def toggle_vumeters(self, widget):
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
                self.vu_list[i][j].set_orientation(Gtk.Orientation.VERTICAL)
                self.vu_list[i][j].set_margin_bottom(8)
                self.vu_list[i][j].set_margin_top(8)
                self.vu_list[i][j].set_vexpand(True)
                self.vu_list[i][j].set_hexpand(True)
                self.vu_list[i][j].set_halign(Gtk.Align.CENTER)

                self.vu_list[i][j].set_inverted(True)
                grid.add(self.vu_list[i][j])
                if self.pulse.config[i][j]['name'] != '':
                    self.vu_thread[i][j] = threading.Thread(target=self.listen_peak, 
                            args=([i, j],))
                    if self.enable_vumeters == True:
                        self.vu_thread[i][j].start() 

    def restart_vumeter(self, index, stop_only=None):
        if self.enable_vumeters == False:
            return
        if stop_only != False:
            if index[1] in self.pulse.vu_list[index[0]] or stop_only == True:
                self.pulse.vu_list[index[0]][index[1]].terminate()
                self.vu_thread[index[0]][index[1]].join()
                self.vu_list[index[0]][index[1]].set_fraction(0)

        if stop_only == True:
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
        self.sink_list = self.pulse.get_hardware_devices('sinks')
        self.source_list = self.pulse.get_hardware_devices('sources')
        for device in ['hi', 'a']:
            name_size = 35 if device == 'a' else 20
            devices = self.sink_list if device == 'a' else self.source_list

            # for each combobox
            found = False
            for j in range(1, 4):
                combobox = self.builder.get_object(f'{device}_{j}_combobox')
                combobox.append_text('')
                for i in range(0, len(devices)):
                    text = devices[i]['description'][:name_size]
                    if len(text) == name_size:
                        text = text + '...'
                    combobox.append_text(text)
                    if devices[i]['name'] == self.pulse.config[device][str(j)]['name']:
                        found = True
                        combobox.set_active(i + 1)

                if found == False:
                    self.pulse.config[device][str(j)]['name'] = ''

                combobox.connect('changed', self.on_combo_changed, [device, str(j)], devices)

    def start_inputs(self):
        self.Rename_Popover = self.builder.get_object('rename_popover')
        self.Popover_Entry = self.builder.get_object('popover_entry')
        self.Popover_Entry.connect('activate', self.label_rename_entry)

        self.vi_primary_buttons = []
        hardware_inputs = self.pulse.get_hardware_devices('sources')
        virtual_inputs = self.pulse.get_virtual_devices('sinks')
        # for each input device
        for i in ['1', '2', '3']:

            name = self.pulse.config['vi'][i]['name']
            label = self.builder.get_object(f'vi_{i}_label')
            label.set_text(name if name != '' else f'Virtual Input {i}')
            label_evt_box = self.builder.get_object(f'vi_{i}_label_event_box')
            label_evt_box.connect('button_press_event', self.label_click, label, ['vi', i])
            primary = self.builder.get_object(f'vi_{i}_primary')
            primary.set_active(self.pulse.config['vi'][i]['primary'])
            if self.pulse.config['vi'][i]['primary'] == True:
                primary.set_sensitive(False)
            primary.connect('toggled', self.toggle_primary, ['vi', i])
            self.vi_primary_buttons.append(primary)

            rnnoise = self.builder.get_object(f'hi_{i}_rnnoise')
            rnnoise.set_active(self.pulse.config['hi'][i]['use_rnnoise'])
            rnnoise.connect('toggled', self.toggle_rnnoise, ['hi', i], f'hi{i}_rnnoise')
            rnnoise.connect('button_press_event', self.open_popover, RnnoisePopover, ['hi', i])

            found = 0
            for path in ['/usr/lib/ladspa', '/usr/local/lib/ladspa']:
                if os.path.isfile(os.path.join(path, 'librnnoise_ladspa.so')): 
                    found = 1
                    break
                elif os.path.isfile(os.path.join(path, 'rnnoise_ladspa.so')):
                    found = 1
                    break

            if found == 0:
                rnnoise.set_visible(False)
                rnnoise.set_no_show_all(True)

            for device in ['hi', 'vi']:

                dev_type = virtual_inputs if device == 'vi' else hardware_inputs
                for dev in dev_type:
                    if dev['name'] == self.pulse.config[device][i]['name']:
                        self.pulse.config[device][i]['vol'] = dev['volume']

                vol = self.builder.get_object(f'{device}_{i}_adjust')
                vol.set_value(self.pulse.config[device][i]['vol'])
                vol.connect('value-changed', self.volume_change, [device, i])

                mute = self.builder.get_object(f'{device}_{i}_mute')
                mute.set_active(self.pulse.config[device][i]['mute'])
                mute.connect('toggled', self.toggle_mute, [device, i])

                scale = self.builder.get_object(f'{device}_{i}_vol')
                scale.add_mark(100, Gtk.PositionType.TOP, '')

                # connection buttons
                for k in ['a', 'b']:
                    for j in ['1', '2', '3']:
                        button = self.builder.get_object(f'{device}_{i}_{k}{j}')
                        button.set_active(self.pulse.config[device][i][k + j])
                        button.connect('toggled', self.toggle_loopback, [k, j], [device, i])
                        button.connect('button_press_event', self.open_popover, LatencyPopover, [device, i, k + j])



    def start_outputs(self):
        self.b_primary_buttons = []
        hardware_outputs = self.pulse.get_hardware_devices('sinks')
        virtual_outputs = self.pulse.get_virtual_devices('sources')
        for i in ['1', '2', '3']:

            primary = self.builder.get_object(f'b_{i}_primary')
            primary.set_active(self.pulse.config['b'][i]['primary'])
            if self.pulse.config['b'][i]['primary'] == True:
                primary.set_sensitive(False)

            primary.connect('toggled', self.toggle_primary, ['b', i])
            self.b_primary_buttons.append(primary)

            for j in ['a', 'b']:
                dev_list = hardware_outputs if j == 'a' else virtual_outputs
                for dev in dev_list:
                    if dev['name'] == self.pulse.config[j][i]['name']:
                        self.pulse.config[j][i]['vol'] = dev['volume']

                master = self.builder.get_object(f'{j}_{i}_adjust')
                master.set_value(self.pulse.config[j][i]['vol'])
                master.connect('value-changed', self.volume_change, [j, i])

                mute = self.builder.get_object(f'{j}_{i}_mute')
                mute.set_active(self.pulse.config[j][i]['mute'])
                mute.connect('toggled', self.toggle_mute, [j, i])

                eq = self.builder.get_object(f'{j}_{i}_eq')
                eq.set_active(self.pulse.config[j][i]['use_eq'])
                eq.connect('toggled', self.toggle_eq, [j, i])
                eq.connect('button_press_event', self.open_popover, EqPopover, [j, i])

                scale = self.builder.get_object(f'{j}_{i}_vol')
                scale.add_mark(100, Gtk.PositionType.TOP, '')

                found = 0
                for path in ['/usr/lib/ladspa', '/usr/local/lib/ladspa']:
                    if os.path.isfile(os.path.join(path, 'mbeq_1197.so')):
                        found = 1
                if found == 0:
                    eq.set_visible(False)
                    eq.set_no_show_all(True)

    def toggle_eq(self, button, index):
        func = self.pulse.apply_eq if button.get_active() == True else self.pulse.remove_eq
        func(index)

    def toggle_rnnoise(self, widget, source_index, sink_name):
        stat = 'connect' if widget.get_active() == True else 'disconnect'
        self.pulse.rnnoise(source_index, sink_name, stat)

    def toggle_mute(self, button, index):
        state = 1 if button.get_active() else 0
        self.pulse.mute(index, state)

    def toggle_loopback(self, button, sink_index, source_index):
        state = 'connect' if button.get_active() else 'disconnect'
        self.pulse.connect(state, source_index, sink_index)

    def volume_change(self, slider, index, stream_type=None):
        val = int(slider.get_value())
        if type(index) == int or self.pulse.config[index[0]][index[1]]['name'] != '':
            self.pulse.volume(index, val, stream_type)

    def open_popover(self, button, event, popover, index):
        if event.button == 3:
            if self.pulse.config[index[0]][index[1]]['name'] != '':
                popover(button, self.pulse, index)

    def label_rename_entry(self, widget):
        name = widget.get_text()
        if not ' ' in name:
            if self.pulse.rename(self.Label_Index, name) == True:
                self.PopActive.set_text(name)
                self.sink_input_box.load_application_list()
                self.source_output_box.load_application_list()

                self.restart_vumeter(self.Label_Index)

        else:
            return

        self.Rename_Popover.popdown()

    def label_click(self, widget, event, label, index):
        self.Label_Index = index
        self.Rename_Popover.set_relative_to(widget)
        self.Rename_Popover.popup()
        self.PopActive = label

    def on_combo_changed(self, widget, index, device):
        model = widget.get_active()

        # if device its not an empty name
        if self.pulse.config[index[0]][index[1]]['name'] != '':
            if index[0] == 'hi':
                self.pulse.disable_source(index[1])
            else:
                self.pulse.disable_sink(index[1])

        # if chosen device is not an empty name
        if model > 0:
            self.pulse.config[index[0]][index[1]]['name'] = device[model - 1]['name']
            if index[0] == 'hi':
                self.pulse.start_source(index[1])
            else:
                self.pulse.start_sink(index[1])
            self.restart_vumeter(index)

        # if its an empty name
        else:
            self.pulse.config[index[0]][index[1]]['name'] = ''
            self.restart_vumeter(index, True)

    def toggle_primary(self, widget, index):
        if widget.get_active() == False:
            return
        else:
            widget.set_sensitive(False)
            button_list = self.vi_primary_buttons if index[0] == 'vi' else self.b_primary_buttons
            for i in range(3):
                if str(i + 1) != index[1]:
                    button_list[i].set_sensitive(True)
                    button_list[i].set_active(False)

        self.pulse.set_primary(index)
        if index[0] == 'vi':
            self.sink_input_box.load_application_list()
        else:
            self.source_output_box.load_application_list()


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
        self.pulse.save_config()
        self.pulse.end_subscribe()
        self.subscribe_thread.join()
        if self.enable_vumeters == True:
            self.pulse.end_vumeter()
            for i in ['hi', 'vi', 'a', 'b']:
                for j in ['1','2','3']:
                    if j in self.vu_thread[i]:
                        self.vu_thread[i][j].join()
        Gtk.main_quit()
        return False
