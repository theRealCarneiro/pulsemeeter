import os
import threading
import sys
import json

from .EqPopover import EqPopover
from .RnnoisePopover import RnnoisePopover
from .LatencyPopover import LatencyPopover
from .settings import GLADEFILE

from gi.repository import Gtk,Gdk,Gio

class MainWindow(Gtk.Window):

    def __init__(self, pulse):

        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        self.pulse = pulse

        component_list = [
                    'window',
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

        self.start_app_list()
        self.start_hardware_comboboxes()
        self.start_inputs()
        self.start_outputs()

        self.Window = self.builder.get_object('window')

        self.Window.connect('delete_event', self.delete_event)

        self.Window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)

        self.Window.show_all()

    def start_app_list(self):
        self.Sink_Input_List = self.builder.get_object('sink_input_list')
        self.Source_Output_List = self.builder.get_object('source_output_list')

        self.sink_input_box_list = []
        self.source_output_box_list = []

        self.load_application_list('sink', self.sink_input_box_list, self.Sink_Input_List)
        self.load_application_list('source', self.source_output_box_list, self.Source_Output_List)

        self.subscribe_thread = threading.Thread(target=self.listen_subscribe, args=())
        self.subscribe_thread.start()

    def start_hardware_comboboxes(self):
        self.sink_list = self.pulse.get_hardware_devices('sinks')
        self.source_list = self.pulse.get_hardware_devices('sources')
        for device in ['hi', 'a']:
            name_size = 35 if device == 'a' else 20
            devices = self.sink_list if device == 'a' else self.source_list

            # for each combobox
            for j in range(1, 4):
                combobox = self.builder.get_object(f'{device}_{j}_combobox')
                combobox.append_text('')
                for i in range(0, len(devices)):
                    text = devices[i]['description'][:name_size]
                    if len(text) == name_size:
                        text = text + '...'
                    combobox.append_text(text)
                    if devices[i]['name'] == self.pulse.config[device][str(j)]['name']:
                        combobox.set_active(i + 1)

                combobox.connect('changed', self.on_combo_changed, [device, str(j)], devices)

    def start_inputs(self):
        self.Rename_Popover = self.builder.get_object('rename_popover')
        self.Popover_Entry = self.builder.get_object('popover_entry')
        self.Popover_Entry.connect('activate', self.label_rename_entry)

        self.vi_primary_buttons = []
        # for each input device
        for i in ['1', '2', '3']:

            name = self.pulse.config['vi'][i]['name']
            label = self.builder.get_object(f'vi_{i}_label')
            label.set_text(name if name != '' else f'Virtual Input {i}')
            label_evt_box = self.builder.get_object(f'vi_{i}_label_event_box')
            label_evt_box.connect('button_press_event', self.label_click, label, ['vi', i])
            primary = self.builder.get_object(f'vi_{i}_primary')
            primary.set_active(self.pulse.config['vi'][i]['primary'])
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
        for i in ['1', '2', '3']:

            primary = self.builder.get_object(f'b_{i}_primary')
            primary.set_active(self.pulse.config['b'][i]['primary'])
            primary.connect('toggled', self.toggle_primary, ['b', i])
            self.b_primary_buttons.append(primary)

            for j in ['a', 'b']:
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

    def volume_change(self, slider, index):
        val = int(slider.get_value())
        self.pulse.volume(index, val)

    def open_popover(self, button, event, popover, index):
        if event.button == 3:
            if self.pulse.config[index[0]][index[1]]['name'] != '':
                popover(button, self.pulse, index)

    def label_rename_entry(self, widget):
        name = widget.get_text()
        if not ' ' in name:
            if self.pulse.rename(self.Label_Index, name) == True:
                self.PopActive.set_text(name)
                self.load_application_list('sink', self.sink_input_box_list, self.Sink_Input_List)
                self.load_application_list('source', self.source_output_box_list, self.Source_Output_List)

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
        if model > 0:
            self.pulse.config[index[0]][index[1]]['name'] = device[model - 1]['name']
        else:
            self.pulse.config[index[0]][index[1]]['name'] = ''

    def toggle_primary(self, widget, index):
        if widget.get_active() == False:
            return
        else:
            button_list = self.vi_primary_buttons if index[0] == 'vi' else self.b_primary_buttons
            for i in range(3):
                if str(i + 1) != index[1]:
                    button_list[i].set_active(False)

        self.pulse.set_primary(index)
        if index[0] == 'vi':
            self.load_application_list('sink', self.sink_input_box_list, self.Sink_Input_List)
        else:
            self.load_application_list('source', self.source_output_box_list, self.Source_Output_List)


    def app_combo_change(self, combobox, dev_type, app):
        name = combobox.get_active_text()
        if dev_type == 'sink':
            self.pulse.move_sink_input(app, name)
        if dev_type == 'source':
            self.pulse.move_source_output(app, name)

    def remove_app_dev(self, box_list, widget, id=None):
        if id == None:
            for i in box_list:
                widget.remove(i[0])
            box_list.clear()
            return

        for i in box_list:
            if str(id) == str(i[1]):
                widget.remove(i[0])
                box_list.remove(i)
                break

    def load_application_list(self, dev_type, box_list, widget, id=None):
        if id == None and len(box_list) > 0:
            self.remove_app_dev(box_list, widget)

        if dev_type == 'source':
            self.app_list = self.pulse.get_source_outputs()
        else:
            self.app_list = self.pulse.get_sink_inputs()

        if len(self.app_list) == 0: 
            return

        name_vi = []
        name_b = []
        for i in ['1','2','3']:
            if dev_type == 'source':
                if self.pulse.config['b'][i]['name'] != '':
                    name_b.append(self.pulse.config['b'][i]['name'])
                if self.pulse.config['vi'][i]['name'] != '':
                    name_vi.append(self.pulse.config['vi'][i]['name'] + '.monitor')
            elif self.pulse.config['vi'][i]['name'] != '':
                    name_vi.append(self.pulse.config['vi'][i]['name'])


        if dev_type == 'source':
            name_b.extend(name_vi)
            dev_list = name_b
        else:
            dev_list = name_vi

        for i in self.app_list:
            if id != None:
                if str(id) != str(i['id']):
                    continue

            icon = Gio.ThemedIcon(name=i['icon'])
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
            label = Gtk.Label(i['name'])
            label.props.halign = Gtk.Align.START
            combobox = Gtk.ComboBoxText()
            for j in range(len(dev_list)):
                combobox.append_text(dev_list[j])
                index = dev_list.index(i['device']) if i['device'] in dev_list else 0
                combobox.set_active(index)
            combobox.connect('changed', self.app_combo_change, dev_type, i['id'])
            combobox.props.halign = Gtk.Align.END
            combobox.set_hexpand(True)

            box = Gtk.Box(spacing=5)
            box.pack_start(image, expand = False, fill = False, padding = 0)
            box.pack_start(label, expand = False, fill = False, padding = 0)
            box.pack_start(combobox, expand = False, fill = True, padding = 0)
            box_list.append([box, i['id']])
            widget.pack_start(box, expand = True, fill = True, padding = 0)

            widget.show_all()

    def listen_subscribe(self):
        for i in self.pulse.subscribe():
            if 'remove' in i:
                id = i.split('#')[1].strip('\n')
                if 'sink-input' in i:
                    self.remove_app_dev(self.sink_input_box_list, self.Sink_Input_List, id)
                elif 'source-output' in i:
                    self.remove_app_dev(self.source_output_box_list, self.Source_Output_List, id)
            elif 'new' in i:
                id = i.split('#')[1].strip('\n')
                if 'sink-input' in i:
                    self.load_application_list('sink', self.sink_input_box_list, self.Sink_Input_List, id)
                elif 'source-output' in i:
                    self.load_application_list('source', self.source_output_box_list, self.Source_Output_List, id)
            # elif 'change' in i:
                # id = i.split('#')[1].strip('\n')
                # if 'sink-input' in i:
                    # self.remove_app_dev(self.sink_input_box_list, self.Sink_Input_List, id)
                    # self.load_application_list('sink', self.sink_input_box_list, self.Sink_Input_List, id)
                # elif 'source-output' in i:
                    # self.remove_app_dev(self.source_output_box_list, self.Source_Output_List, id)
                    # self.load_application_list('source', self.source_output_box_list, self.Source_Output_List, id)

    def delete_event(self, widget, event):
        self.pulse.save_config()
        self.pulse.end_subscribe()
        self.subscribe_thread.join()
        Gtk.main_quit()
        return False
