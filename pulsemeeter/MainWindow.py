import os
import sys
import json
from pathlib import Path

from .EqPopover import EqPopover
from .RnnoisePopover import RnnoisePopover
from .LatencyPopover import LatencyPopover
from .settings import GLADEFILE

from gi.repository import Gtk,Gdk

class MainWindow(Gtk.Window):

    def __init__(self, pulse):

        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        self.pulse = pulse

        component_list = [
                    'Window',
                    'Popover',
                    'Popover_Entry',
                    'Latency_Popover',
                    'Latency_Adjust',
                    'Rnnoise_Popover',
                    'Rnnoise_Latency_Adjust',
                    'Rnnoise_Threshold_Adjust',
                ]
        for i in range(1, 4):
            component_list.append(f'Hardware_Input_{i}_Adjust')
            component_list.append(f'Virtual_Input_{i}_Adjust')
            component_list.append(f'Master_A{i}_Adjust')
            component_list.append(f'Master_B{i}_Adjust')

            # component_list.append(f'A{i}_Combobox')
            # component_list.append(f'Hardware_Input_{i}_Combobox')
            # component_list.append(f'Hardware_Input_{i}_Rnnoise')
            # component_list.append(f'Virtual_Input_{i}_Label')
            # for j in range(1, 4):
                # component_list.append(f'Hardware_Input_{i}_A{j}')
                # component_list.append(f'Hardware_Input_{i}_B{j}')
                # component_list.append(f'Virtual_Input_{i}_A{j}')
                # component_list.append(f'Virtual_Input_{i}_B{j}')
                # component_list.append(f'Mute_A{j}')
                # component_list.append(f'Mute_B{j}')
                # component_list.append(f'EQ_A{j}')
                # component_list.append(f'EQ_B{j}')

        try:
            self.builder.add_objects_from_file(
                GLADEFILE,
                component_list
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.Popover = self.builder.get_object('Popover')
        self.Popover_Entry = self.builder.get_object('Popover_Entry')
        self.Popover_Entry.connect('activate', self.label_rename_entry)

        # start comboboxes
        for device in ['Hardware_Input_', 'A']:
            if device == 'A':
                dev_type = 'sinks'
                dev_name = 'a'
                dev_size = 35
            else:
                dev_type = 'sources'
                dev_name = 'hi'
                dev_size = 20

            devices = self.pulse.get_hardware_devices(dev_type)

            # for each combobox
            for j in range(1, 4):
                combobox = self.builder.get_object(f'{device}{j}_Combobox')
                combobox.append_text('')
                for i in range(0, len(devices)):
                    text = devices[i][1][:dev_size]
                    if len(text) == dev_size:
                        text = text + '...'
                    combobox.append_text(text)
                    if devices[i][0] == self.pulse.config[dev_name][str(j)]['name']:
                        combobox.set_active(i + 1)

                combobox.connect('changed', self.on_combo_changed, [dev_name, str(j)], devices)

        # start inputs
        for device in ['Hardware_Input', 'Virtual_Input']:

            # for each input device
            for i in ['1', '2', '3']:

                # for each output
                for j in ['1', '2', '3']:

                    # connection buttons
                    for k in ['a', 'b']:
                        dev_type = 'vi' if device == 'Virtual_Input' else 'hi'
                        button = self.builder.get_object(f'{device}_{i}_{k.upper()}{j}')
                        button.set_active(self.pulse.config[dev_type][i][k + j])
                        button.connect('toggled', self.toggle_loopback, [k, j], [dev_type, i])
                        button.connect('button_press_event', self.open_popover, LatencyPopover, [dev_type, i, k + j])

                    vol = self.builder.get_object(f'{device}_{i}_Adjust')
                    vol.set_value(self.pulse.config[dev_type][i]['vol'])
                    vol.connect('value-changed', self.volume_change, [dev_type, i])

                if device == 'Virtual_Input':
                    name = self.pulse.config['vi'][i]['name']
                    label = self.builder.get_object(f'Virtual_Input_{i}_Label')
                    label.set_text(name if name != '' else f'Virtual Input {i}')

                    label_evt_box = self.builder.get_object(f'Virtual_Input_{i}_Label_Event_Box')
                    label_evt_box.connect('button_press_event', self.label_click, label, ['vi', i])
                else:
                    rnnoise = self.builder.get_object(f'Hardware_Input_{i}_Rnnoise')
                    rnnoise.set_active(self.pulse.config['hi'][i]['use_rnnoise'])
                    rnnoise.connect('toggled', self.toggle_rnnoise, ['hi', i], f'hi{i}_rnnoise')
                    rnnoise.connect('button_press_event', self.open_popover, RnnoisePopover, ['hi', i])

                    found = 0
                    for path in ['/usr/lib/ladspa', '/usr/local/lib/ladspa']:
                        if os.path.isfile(os.path.join(path, 'librnnoise_ladspa.so', path, 'rnnoise_ladspa.so')):
                            found = 1
                            break
                    if found == 0:
                        rnnoise.set_visible(False)
                        rnnoise.set_no_show_all(True)

        # start outputs
        for i in ['1', '2', '3']:
            for j in ['a', 'b']:
                master = self.builder.get_object(f'Master_{j.upper()}{i}_Adjust')
                master.set_value(self.pulse.config[j][i]['vol'])
                master.connect('value-changed', self.volume_change, [j, i])

                mute = self.builder.get_object(f'Mute_{j.upper()}{i}')
                mute.set_active(self.pulse.config[j][i]['mute'])
                mute.connect('toggled', self.toggle_mute, [j, i])

                eq = self.builder.get_object(f'EQ_{j.upper()}{i}')
                eq.set_active(self.pulse.config[j][i]['use_eq'])
                eq.connect('toggled', self.toggle_eq, [j, i])
                eq.connect('button_press_event', self.open_popover, EqPopover, [j, i])

                found = 0
                for path in ['/usr/lib/ladspa', '/usr/local/lib/ladspa']:
                    if os.path.isfile(os.path.join(path, 'mbeq_1197.so')):
                        found = 1
                if found == 0:
                    eq.set_visible(False)
                    eq.set_no_show_all(True)

        self.Window = self.builder.get_object('Window')

        self.Window.connect('delete_event', self.delete_event)

        self.Window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)

        self.Window.show_all()


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

    def volume_change(self, slider, index):
        val = int(slider.get_value())
        self.pulse.volume(index, val)

    def open_popover(self, button, event, popover, index):
        if event.button == 3:
            if self.pulse.config[index[0]][index[1]]['name'] != '':
                popover(button, self.pulse, index)

    def label_rename_entry(self, widget):
        name = widget.get_text()
        if self.pulse.rename(self.Label_Index, name) == True:
            self.PopActive.set_text(name)

        self.Popover.popdown()

    def label_click(self, widget, event, label, index):
        self.Label_Index = index
        self.Popover.set_relative_to(widget)
        self.Popover.popup()
        self.PopActive = label

    def on_combo_changed(self, widget, index, device):
        model = widget.get_active()
        if model > 0:
            self.pulse.config[index[0]][index[1]]['name'] = device[model - 1][0]
        else:
            self.pulse.config[index[0]][index[1]]['name'] = ''

    def delete_event(self, widget, event):
        self.pulse.save_config()
        Gtk.main_quit()
        return False

