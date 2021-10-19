import os
import shutil
import sys
import json
from pathlib import Path
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class MainWindow(Gtk.Window):

    def __init__(self, config, pulse):
        self.config = config
        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        
        gladefile = ''
        # gladefile = get_config_path(True)
        # if not os.path.exists(gladefile):
        gladefile = '/usr/local/lib/python3.9/site-packages/pulsemeeter/Interface.glade'
        if not os.path.exists(gladefile):
            gladefile = '/usr/lib/python3.9/site-packages/pulsemeeter/Interface.glade'
            if not os.path.exists(gladefile):
                gladefile = get_config_path(True)
                # else:
                    # shutil.copy(gladefile, get_config_path(True))
            # else:
                # shutil.copy(gladefile, get_config_path(True))
        self.gladefile = gladefile

        try:
            self.builder.add_objects_from_file(
                gladefile,
                [
                    'Popover',
                    'Popover_Entry',
                    'Latency_Popover',
                    'Latency_Adjust',
                    'Noisetorch_Popover',
                    'Noisetorch_Latency_Adjust',
                    'Noisetorch_Threshold_Adjust',
                    'A1_Combobox',
                    'A2_Combobox',
                    'A3_Combobox',

                    'Hardware_Input_1_Combobox',
                    'Hardware_Input_2_Combobox',
                    'Hardware_Input_3_Combobox',

                    'Hardware_Input_1_Noisetorch',
                    'Hardware_Input_2_Noisetorch',
                    'Hardware_Input_3_Noisetorch',

                    'Hardware_Input_1_Adjust',
                    'Hardware_Input_1_A1',
                    'Hardware_Input_1_A2',
                    'Hardware_Input_1_A3',
                    'Hardware_Input_1_B1',
                    'Hardware_Input_1_B2',
                    'Hardware_Input_1_B3',

                    'Hardware_Input_2_Adjust',
                    'Hardware_Input_2_A1',
                    'Hardware_Input_2_A2',
                    'Hardware_Input_2_A3',
                    'Hardware_Input_2_B1',
                    'Hardware_Input_2_B2',
                    'Hardware_Input_2_B3',

                    'Hardware_Input_3_Adjust',
                    'Hardware_Input_3_A1',
                    'Hardware_Input_3_A2',
                    'Hardware_Input_3_A3',
                    'Hardware_Input_3_B1',
                    'Hardware_Input_3_B2',
                    'Hardware_Input_3_B3',

                    'Virtual_Input_1_Adjust',
                    'Virtual_Input_1_A1',
                    'Virtual_Input_1_A2',
                    'Virtual_Input_1_A3',
                    'Virtual_Input_1_B1',
                    'Virtual_Input_1_B2',
                    'Virtual_Input_1_B3',

                    'Virtual_Input_2_Adjust',
                    'Virtual_Input_2_A1',
                    'Virtual_Input_2_A2',
                    'Virtual_Input_2_A3',
                    'Virtual_Input_2_B1',
                    'Virtual_Input_2_B2',
                    'Virtual_Input_2_B3',

                    'Virtual_Input_3_Adjust',
                    'Virtual_Input_3_A1',
                    'Virtual_Input_3_A2',
                    'Virtual_Input_3_A3',
                    'Virtual_Input_3_B1',
                    'Virtual_Input_3_B2',
                    'Virtual_Input_3_B3',

                    'Mute_A1',
                    'Mute_A2',
                    'Mute_A3',
                    'Mute_B1',
                    'Mute_B2',
                    'Mute_B3',

                    'EQ_A1',
                    'EQ_A2',
                    'EQ_A3',
                    'EQ_B1',
                    'EQ_B2',
                    'EQ_B3',

                    'Master_A1_Adjust',
                    'Master_A2_Adjust',
                    'Master_A3_Adjust',
                    'Master_B1_Adjust',
                    'Master_B2_Adjust',
                    'Master_B3_Adjust',

                    'Window'
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.pulse = pulse
        self.init = True

        self.src_list = Gtk.ListStore(str)
        self.src_concat = self.pulse.get_hardware_devices("sources")

        self.Hardware_Input_1_Combobox = self.builder.get_object('Hardware_Input_1_Combobox')
        self.Hardware_Input_2_Combobox = self.builder.get_object('Hardware_Input_2_Combobox')
        self.Hardware_Input_3_Combobox = self.builder.get_object('Hardware_Input_3_Combobox')

        self.Hardware_Input_1_Combobox.append_text("")
        self.Hardware_Input_2_Combobox.append_text("")
        self.Hardware_Input_3_Combobox.append_text("")
        for device in self.src_concat:
            self.Hardware_Input_1_Combobox.append_text(device[1][:20] + '...')
            self.Hardware_Input_2_Combobox.append_text(device[1][:20] + '...')
            self.Hardware_Input_3_Combobox.append_text(device[1][:20] + '...')

        index = [-1, -1, -1]
        for j in range(1, 4):
            for i in range(0, len(self.src_concat)):
                if self.src_concat[i][0] == self.config['hi'][str(j)]['name']:
                    index[j - 1] = i + 1
                    break;

        self.Hardware_Input_1_Combobox.set_active(index[0])
        self.Hardware_Input_2_Combobox.set_active(index[1])
        self.Hardware_Input_3_Combobox.set_active(index[2])
        self.Hardware_Input_1_Combobox.connect("changed", self.on_combo_changed, ['hi','1'], self.src_concat)
        self.Hardware_Input_2_Combobox.connect("changed", self.on_combo_changed, ['hi','2'], self.src_concat)
        self.Hardware_Input_3_Combobox.connect("changed", self.on_combo_changed, ['hi','3'], self.src_concat)

        self.device_list = Gtk.ListStore(str)
        self.devices_concat = self.pulse.get_hardware_devices("sinks")

        self.A1_Combobox = self.builder.get_object('A1_Combobox')
        self.A2_Combobox = self.builder.get_object('A2_Combobox')
        self.A3_Combobox = self.builder.get_object('A3_Combobox')

        self.A1_Combobox.append_text("")
        self.A2_Combobox.append_text("")
        self.A3_Combobox.append_text("")
        for device in self.devices_concat:
            self.A1_Combobox.append_text(device[1])
            self.A2_Combobox.append_text(device[1])
            self.A3_Combobox.append_text(device[1])

        index = [-1, -1, -1]
        for j in range(1, 4):
            for i in range(0, len(self.devices_concat)):
                if self.devices_concat[i][0] == self.config['a'][str(j)]['name']:
                    index[j - 1] = i + 1
                    break;

        self.A1_Combobox.set_active(index[0])
        self.A2_Combobox.set_active(index[1])
        self.A3_Combobox.set_active(index[2])
        self.A1_Combobox.connect("changed", self.on_combo_changed, ['a','1'], self.devices_concat)
        self.A2_Combobox.connect("changed", self.on_combo_changed, ['a','2'], self.devices_concat)
        self.A3_Combobox.connect("changed", self.on_combo_changed, ['a','3'], self.devices_concat)

        self.Hardware_Input_1_Adjust = self.builder.get_object('Hardware_Input_1_Adjust')
        self.Hardware_Input_1_Adjust.set_value(self.config['hi']['1']['vol'])
        self.Hardware_Input_1_Adjust.connect('value-changed', self.slider_change, "source", ['hi', '1']) # self.config['hi']['1']['name'], ['vol','hi','1'])
        self.Hardware_Input_1_Noisetorch = self.builder.get_object('Hardware_Input_1_Noisetorch')
        self.Hardware_Input_2_Noisetorch = self.builder.get_object('Hardware_Input_2_Noisetorch')
        self.Hardware_Input_3_Noisetorch = self.builder.get_object('Hardware_Input_3_Noisetorch')

        self.Hardware_Input_1_Noisetorch.set_active(self.config['hi']['1']['use_rnnoise'])
        self.Hardware_Input_2_Noisetorch.set_active(self.config['hi']['2']['use_rnnoise'])
        self.Hardware_Input_3_Noisetorch.set_active(self.config['hi']['3']['use_rnnoise'])

        self.Hardware_Input_1_Noisetorch.connect('toggled', self.rnnoise_toggle, ['hi', '1'], 'hi1_rnnoise')
        self.Hardware_Input_2_Noisetorch.connect('toggled', self.rnnoise_toggle, ['hi', '2'], 'hi2_rnnoise')
        self.Hardware_Input_3_Noisetorch.connect('toggled', self.rnnoise_toggle, ['hi', '3'], 'hi3_rnnoise')

        self.Hardware_Input_1_Noisetorch.connect("button_press_event", self.rnnoise_popop, ['hi', '1'])
        self.Hardware_Input_2_Noisetorch.connect("button_press_event", self.rnnoise_popop, ['hi', '2'])
        self.Hardware_Input_3_Noisetorch.connect("button_press_event", self.rnnoise_popop, ['hi', '3'])

        self.Hardware_Input_1_A1 = self.builder.get_object('Hardware_Input_1_A1')
        self.Hardware_Input_1_A2 = self.builder.get_object('Hardware_Input_1_A2')
        self.Hardware_Input_1_A3 = self.builder.get_object('Hardware_Input_1_A3')
        self.Hardware_Input_1_B1 = self.builder.get_object('Hardware_Input_1_B1')
        self.Hardware_Input_1_B2 = self.builder.get_object('Hardware_Input_1_B2')
        self.Hardware_Input_1_B3 = self.builder.get_object('Hardware_Input_1_B3')
        self.Hardware_Input_1_A1.set_active(self.config['hi']['1']['a1'])
        self.Hardware_Input_1_A2.set_active(self.config['hi']['1']['a2'])
        self.Hardware_Input_1_A3.set_active(self.config['hi']['1']['a3'])
        self.Hardware_Input_1_B1.set_active(self.config['hi']['1']['b1'])
        self.Hardware_Input_1_B2.set_active(self.config['hi']['1']['b2'])
        self.Hardware_Input_1_B3.set_active(self.config['hi']['1']['b3'])
        self.Hardware_Input_1_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['hi', '1'])
        self.Hardware_Input_1_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['hi', '1'])
        self.Hardware_Input_1_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['hi', '1'])
        self.Hardware_Input_1_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['hi', '1'])
        self.Hardware_Input_1_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['hi', '1'])
        self.Hardware_Input_1_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['hi', '1'])

        self.Hardware_Input_1_A1.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'a1'])
        self.Hardware_Input_1_A2.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'a2'])
        self.Hardware_Input_1_A3.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'a3'])
        self.Hardware_Input_1_B1.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'b1'])
        self.Hardware_Input_1_B2.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'b2'])
        self.Hardware_Input_1_B3.connect("button_press_event", self.loopback_latency_popop, ['hi', '1', 'b3'])

        self.Hardware_Input_2_Label = self.builder.get_object('Hardware_Input_2')
        self.Hardware_Input_2_Adjust = self.builder.get_object('Hardware_Input_2_Adjust')
        self.Hardware_Input_2_Adjust.set_value(self.config['hi']['2']['vol'])
        self.Hardware_Input_2_Adjust.connect('value-changed', self.slider_change, "source", ['hi', '2'])
        self.Hardware_Input_2_A1 = self.builder.get_object('Hardware_Input_2_A1')
        self.Hardware_Input_2_A2 = self.builder.get_object('Hardware_Input_2_A2')
        self.Hardware_Input_2_A3 = self.builder.get_object('Hardware_Input_2_A3')
        self.Hardware_Input_2_B1 = self.builder.get_object('Hardware_Input_2_B1')
        self.Hardware_Input_2_B2 = self.builder.get_object('Hardware_Input_2_B2')
        self.Hardware_Input_2_B3 = self.builder.get_object('Hardware_Input_2_B3')
        self.Hardware_Input_2_A1.set_active(self.config['hi']['2']['a1'])
        self.Hardware_Input_2_A2.set_active(self.config['hi']['2']['a2'])
        self.Hardware_Input_2_A3.set_active(self.config['hi']['2']['a3'])
        self.Hardware_Input_2_B1.set_active(self.config['hi']['2']['b1'])
        self.Hardware_Input_2_B2.set_active(self.config['hi']['2']['b2'])
        self.Hardware_Input_2_B3.set_active(self.config['hi']['2']['b3'])
        self.Hardware_Input_2_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['hi', '2'])
        self.Hardware_Input_2_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['hi', '2'])
        self.Hardware_Input_2_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['hi', '2'])
        self.Hardware_Input_2_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['hi', '2'])
        self.Hardware_Input_2_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['hi', '2'])
        self.Hardware_Input_2_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['hi', '2'])

        self.Hardware_Input_2_A1.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'a1'])
        self.Hardware_Input_2_A2.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'a2'])
        self.Hardware_Input_2_A3.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'a3'])
        self.Hardware_Input_2_B1.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'b1'])
        self.Hardware_Input_2_B2.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'b2'])
        self.Hardware_Input_2_B3.connect("button_press_event", self.loopback_latency_popop, ['hi', '2', 'b3'])

        self.Hardware_Input_3_Label = self.builder.get_object('Hardware_Input_3')
        self.Hardware_Input_3_Adjust = self.builder.get_object('Hardware_Input_3_Adjust')
        self.Hardware_Input_3_Adjust.set_value(self.config['hi']['3']['vol'])
        self.Hardware_Input_3_Adjust.connect('value-changed', self.slider_change, "source", ['hi', '3'])
        self.Hardware_Input_3_A1 = self.builder.get_object('Hardware_Input_3_A1')
        self.Hardware_Input_3_A2 = self.builder.get_object('Hardware_Input_3_A2')
        self.Hardware_Input_3_A3 = self.builder.get_object('Hardware_Input_3_A3')
        self.Hardware_Input_3_B1 = self.builder.get_object('Hardware_Input_3_B1')
        self.Hardware_Input_3_B2 = self.builder.get_object('Hardware_Input_3_B2')
        self.Hardware_Input_3_B3 = self.builder.get_object('Hardware_Input_3_B3')
        self.Hardware_Input_3_A1.set_active(self.config['hi']['3']['a1'])
        self.Hardware_Input_3_A2.set_active(self.config['hi']['3']['a2'])
        self.Hardware_Input_3_A3.set_active(self.config['hi']['3']['a3'])
        self.Hardware_Input_3_B1.set_active(self.config['hi']['3']['b1'])
        self.Hardware_Input_3_B2.set_active(self.config['hi']['3']['b2'])
        self.Hardware_Input_3_B3.set_active(self.config['hi']['3']['b3'])
        self.Hardware_Input_3_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['hi', '3'])
        self.Hardware_Input_3_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['hi', '3'])
        self.Hardware_Input_3_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['hi', '3'])
        self.Hardware_Input_3_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['hi', '3'])
        self.Hardware_Input_3_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['hi', '3'])
        self.Hardware_Input_3_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['hi', '3'])

        self.Hardware_Input_3_A1.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'a1'])
        self.Hardware_Input_3_A2.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'a2'])
        self.Hardware_Input_3_A3.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'a3'])
        self.Hardware_Input_3_B1.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'b1'])
        self.Hardware_Input_3_B2.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'b2'])
        self.Hardware_Input_3_B3.connect("button_press_event", self.loopback_latency_popop, ['hi', '3', 'b3'])

        
        self.Popover = self.builder.get_object('Popover')
        self.Popover_Entry = self.builder.get_object('Popover_Entry')
        self.Popover_Entry.connect('activate', self.set_popup_entry)

        self.Virtual_Input_1_Label = self.builder.get_object('Virtual_Input_1_Label')
        self.Virtual_Input_1_Label_Event_Box = self.builder.get_object('Virtual_Input_1_Label_Event_Box')
        self.Virtual_Input_1_Label_Event_Box.connect('button_press_event', self.label_click, self.Virtual_Input_1_Label, ['vi', '1'])
        self.Virtual_Input_1_Label.set_text(self.config['vi']['1']['name'] if self.config['vi']['1']['name'] != '' else 'Hardware_Input_1')

        self.Virtual_Input_1_Adjust = self.builder.get_object('Virtual_Input_1_Adjust')
        self.Virtual_Input_1_Adjust.set_value(self.config['vi']['1']['vol'])
        self.Virtual_Input_1_Adjust.connect('value-changed', self.slider_change, "sink", ['vi', '1'])

        self.Virtual_Input_1_A1 = self.builder.get_object('Virtual_Input_1_A1')
        self.Virtual_Input_1_A2 = self.builder.get_object('Virtual_Input_1_A2')
        self.Virtual_Input_1_A3 = self.builder.get_object('Virtual_Input_1_A3')
        self.Virtual_Input_1_B1 = self.builder.get_object('Virtual_Input_1_B1')
        self.Virtual_Input_1_B2 = self.builder.get_object('Virtual_Input_1_B2')
        self.Virtual_Input_1_B3 = self.builder.get_object('Virtual_Input_1_B3')
        self.Virtual_Input_1_A1.set_active(self.config['vi']['1']['a1'])
        self.Virtual_Input_1_A2.set_active(self.config['vi']['1']['a2'])
        self.Virtual_Input_1_A3.set_active(self.config['vi']['1']['a3'])
        self.Virtual_Input_1_B1.set_active(self.config['vi']['1']['b1'])
        self.Virtual_Input_1_B2.set_active(self.config['vi']['1']['b2'])
        self.Virtual_Input_1_B3.set_active(self.config['vi']['1']['b3'])
        self.Virtual_Input_1_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['vi', '1'])
        self.Virtual_Input_1_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['vi', '1'])
        self.Virtual_Input_1_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['vi', '1'])
        self.Virtual_Input_1_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['vi', '1'])
        self.Virtual_Input_1_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['vi', '1'])
        self.Virtual_Input_1_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['vi', '1'])

        self.Virtual_Input_1_A1.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'a1'])
        self.Virtual_Input_1_A2.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'a2'])
        self.Virtual_Input_1_A3.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'a3'])
        self.Virtual_Input_1_B1.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'b1'])
        self.Virtual_Input_1_B2.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'b2'])
        self.Virtual_Input_1_B3.connect("button_press_event", self.loopback_latency_popop, ['vi', '1', 'b3'])

        

        self.Virtual_Input_2_Label = self.builder.get_object('Virtual_Input_2_Label')
        self.Virtual_Input_2_Label_Event_Box = self.builder.get_object('Virtual_Input_2_Label_Event_Box')
        self.Virtual_Input_2_Label_Event_Box.connect('button_press_event', self.label_click, self.Virtual_Input_2_Label, ['vi', '2'])
        self.Virtual_Input_2_Label.set_text(self.config['vi']['2']['name'] if self.config['vi']['2']['name'] != '' else 'Hardware_Input_2')

        self.Virtual_Input_2_Adjust = self.builder.get_object('Virtual_Input_2_Adjust')
        self.Virtual_Input_2_Adjust.set_value(self.config['vi']['2']['vol'])
        self.Virtual_Input_2_Adjust.connect('value-changed', self.slider_change, "sink", ['vi', '2'])

        self.Virtual_Input_2_A1 = self.builder.get_object('Virtual_Input_2_A1')
        self.Virtual_Input_2_A2 = self.builder.get_object('Virtual_Input_2_A2')
        self.Virtual_Input_2_A3 = self.builder.get_object('Virtual_Input_2_A3')
        self.Virtual_Input_2_B1 = self.builder.get_object('Virtual_Input_2_B1')
        self.Virtual_Input_2_B2 = self.builder.get_object('Virtual_Input_2_B2')
        self.Virtual_Input_2_B3 = self.builder.get_object('Virtual_Input_2_B3')
        self.Virtual_Input_2_A1.set_active(self.config['vi']['2']['a1'])
        self.Virtual_Input_2_A2.set_active(self.config['vi']['2']['a2'])
        self.Virtual_Input_2_A3.set_active(self.config['vi']['2']['a3'])
        self.Virtual_Input_2_B1.set_active(self.config['vi']['2']['b1'])
        self.Virtual_Input_2_B2.set_active(self.config['vi']['2']['b2'])
        self.Virtual_Input_2_B3.set_active(self.config['vi']['2']['b3'])
        self.Virtual_Input_2_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['vi', '2'])
        self.Virtual_Input_2_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['vi', '2'])
        self.Virtual_Input_2_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['vi', '2'])
        self.Virtual_Input_2_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['vi', '2'])
        self.Virtual_Input_2_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['vi', '2'])
        self.Virtual_Input_2_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['vi', '2'])

        self.Virtual_Input_2_A1.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'a1'])
        self.Virtual_Input_2_A2.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'a2'])
        self.Virtual_Input_2_A3.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'a3'])
        self.Virtual_Input_2_B1.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'b1'])
        self.Virtual_Input_2_B2.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'b2'])
        self.Virtual_Input_2_B3.connect("button_press_event", self.loopback_latency_popop, ['vi', '2', 'b3'])

        self.Virtual_Input_3_Label = self.builder.get_object('Virtual_Input_3_Label')
        self.Virtual_Input_3_Label_Event_Box = self.builder.get_object('Virtual_Input_3_Label_Event_Box')
        self.Virtual_Input_3_Label_Event_Box.connect('button_press_event', self.label_click, self.Virtual_Input_3_Label, ['vi', '3'])
        self.Virtual_Input_3_Label.set_text(self.config['vi']['3']['name'] if self.config['vi']['3']['name'] != '' else 'Hardware_Input_3')
        self.Virtual_Input_3_Adjust = self.builder.get_object('Virtual_Input_3_Adjust')
        self.Virtual_Input_3_Adjust.set_value(self.config['vi']['3']['vol'])
        self.Virtual_Input_3_Adjust.connect('value-changed', self.slider_change, "sink", ['vi', '3'])
        self.Virtual_Input_3_A1 = self.builder.get_object('Virtual_Input_3_A1')
        self.Virtual_Input_3_A2 = self.builder.get_object('Virtual_Input_3_A2')
        self.Virtual_Input_3_A3 = self.builder.get_object('Virtual_Input_3_A3')
        self.Virtual_Input_3_B1 = self.builder.get_object('Virtual_Input_3_B1')
        self.Virtual_Input_3_B2 = self.builder.get_object('Virtual_Input_3_B2')
        self.Virtual_Input_3_B3 = self.builder.get_object('Virtual_Input_3_B3')
        self.Virtual_Input_3_A1.set_active(self.config['vi']['3']['a1'])
        self.Virtual_Input_3_A2.set_active(self.config['vi']['3']['a2'])
        self.Virtual_Input_3_A3.set_active(self.config['vi']['3']['a3'])
        self.Virtual_Input_3_B1.set_active(self.config['vi']['3']['b1'])
        self.Virtual_Input_3_B2.set_active(self.config['vi']['3']['b2'])
        self.Virtual_Input_3_B3.set_active(self.config['vi']['3']['b3'])
        self.Virtual_Input_3_A1.connect("toggled", self.loopback_toggle, ['a', '1'], ['vi', '3'])
        self.Virtual_Input_3_A2.connect("toggled", self.loopback_toggle, ['a', '2'], ['vi', '3'])
        self.Virtual_Input_3_A3.connect("toggled", self.loopback_toggle, ['a', '3'], ['vi', '3'])
        self.Virtual_Input_3_B1.connect("toggled", self.loopback_toggle, ['b', '1'], ['vi', '3'])
        self.Virtual_Input_3_B2.connect("toggled", self.loopback_toggle, ['b', '2'], ['vi', '3'])
        self.Virtual_Input_3_B3.connect("toggled", self.loopback_toggle, ['b', '3'], ['vi', '3'])

        self.Virtual_Input_3_A1.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'a1'])
        self.Virtual_Input_3_A2.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'a2'])
        self.Virtual_Input_3_A3.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'a3'])
        self.Virtual_Input_3_B1.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'b1'])
        self.Virtual_Input_3_B2.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'b2'])
        self.Virtual_Input_3_B3.connect("button_press_event", self.loopback_latency_popop, ['vi', '3', 'b3'])


        self.Master_A1_Adjust = self.builder.get_object('Master_A1_Adjust')
        self.Master_A3_Adjust = self.builder.get_object('Master_A3_Adjust')
        self.Master_A2_Adjust = self.builder.get_object('Master_A2_Adjust')

        self.Master_A1_Adjust.set_value(self.config['a']['1']['vol'])
        self.Master_A2_Adjust.set_value(self.config['a']['2']['vol'])
        self.Master_A3_Adjust.set_value(self.config['a']['3']['vol'])

        self.Master_A1_Adjust.connect('value-changed', self.slider_change, "sink", ['a', '1'])
        self.Master_A2_Adjust.connect('value-changed', self.slider_change, "sink", ['a', '2'])
        self.Master_A3_Adjust.connect('value-changed', self.slider_change, "sink", ['a', '3'])


        self.Master_B1_Adjust = self.builder.get_object('Master_B1_Adjust')
        self.Master_B2_Adjust = self.builder.get_object('Master_B2_Adjust')
        self.Master_B3_Adjust = self.builder.get_object('Master_B3_Adjust')

        self.Master_B1_Adjust.set_value(self.config['b']['1']['vol'])
        self.Master_B2_Adjust.set_value(self.config['b']['2']['vol'])
        self.Master_B3_Adjust.set_value(self.config['b']['3']['vol'])
        self.Master_B1_Adjust.connect('value-changed', self.slider_change, "source", ['b', '1'])
        self.Master_B2_Adjust.connect('value-changed', self.slider_change, "source", ['b', '2'])
        self.Master_B3_Adjust.connect('value-changed', self.slider_change, "source", ['b', '3'])

        self.EQ_A1 = self.builder.get_object('EQ_A1')
        self.EQ_A2 = self.builder.get_object('EQ_A2')
        self.EQ_A3 = self.builder.get_object('EQ_A3')
        self.EQ_A1.set_active(self.config['a']['1']['use_eq'])
        self.EQ_A2.set_active(self.config['a']['2']['use_eq'])
        self.EQ_A3.set_active(self.config['a']['3']['use_eq'])
        self.EQ_A1.connect('toggled', self.toggle_eq, ['a', '1'], 'A1_EQ')
        self.EQ_A2.connect('toggled', self.toggle_eq, ['a', '2'], 'A2_EQ')
        self.EQ_A3.connect('toggled', self.toggle_eq, ['a', '3'], 'A3_EQ')
        self.EQ_A1.connect('button_press_event', self.open_eq, ['a', '1'], 'A1_EQ')
        self.EQ_A2.connect('button_press_event', self.open_eq, ['a', '2'], 'A2_EQ')
        self.EQ_A3.connect('button_press_event', self.open_eq, ['a', '3'], 'A3_EQ')

        self.EQ_B1 = self.builder.get_object('EQ_B1')
        self.EQ_B2 = self.builder.get_object('EQ_B2')
        self.EQ_B3 = self.builder.get_object('EQ_B3')
        self.EQ_B1.set_active(self.config['b']['1']['use_eq'])
        self.EQ_B2.set_active(self.config['b']['2']['use_eq'])
        self.EQ_B3.set_active(self.config['b']['3']['use_eq'])
        self.EQ_B1.connect('toggled', self.toggle_eq, ['b', '1'], 'B1_EQ')
        self.EQ_B2.connect('toggled', self.toggle_eq, ['b', '2'], 'B2_EQ')
        self.EQ_B3.connect('toggled', self.toggle_eq, ['b', '3'], 'B3_EQ')
        self.EQ_B1.connect('button_press_event', self.open_eq, ['b', '1'], 'B1_EQ')
        self.EQ_B2.connect('button_press_event', self.open_eq, ['b', '2'], 'B2_EQ')
        self.EQ_B3.connect('button_press_event', self.open_eq, ['b', '3'], 'B3_EQ')

        self.Mute_A1 = self.builder.get_object('Mute_A1')
        self.Mute_A2 = self.builder.get_object('Mute_A2')
        self.Mute_A3 = self.builder.get_object('Mute_A3')
        self.Mute_A1.set_active(self.config['a']['1']['mute'])
        self.Mute_A2.set_active(self.config['a']['2']['mute'])
        self.Mute_A3.set_active(self.config['a']['3']['mute'])
        self.Mute_A1.connect('toggled', self.mute_toggle, ['a', '1'], 'sink')
        self.Mute_A2.connect('toggled', self.mute_toggle, ['a', '2'], 'sink')
        self.Mute_A3.connect('toggled', self.mute_toggle, ['a', '3'], 'sink')

        self.Mute_B1 = self.builder.get_object('Mute_B1')
        self.Mute_B2 = self.builder.get_object('Mute_B2')
        self.Mute_B3 = self.builder.get_object('Mute_B3')
        self.Mute_B1.set_active(self.config['b']['1']['mute'])
        self.Mute_B2.set_active(self.config['b']['2']['mute'])
        self.Mute_B3.set_active(self.config['b']['3']['mute'])
        self.Mute_B1.connect('toggled', self.mute_toggle, ['b', '1'], 'source')
        self.Mute_B2.connect('toggled', self.mute_toggle, ['b', '2'], 'source')
        self.Mute_B3.connect('toggled', self.mute_toggle, ['b', '3'], 'source')
        self.init = False


        self.Window = self.builder.get_object('Window')

        self.Window.connect("delete_event", self.delete_event, self.config)

        self.Window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.builder.connect_signals(self)
        self.Window.show_all()


    def slider_change(self, slider, device_type, index):
        val = int(slider.get_value())
        self.pulse.volume(self.config, device_type, index, val)

    def toggle_eq(self, button, index, name):
        command = ''
        if button.get_active() == True:
            control = self.config[index[0]][index[1]]['eq_control']
            self.pulse.apply_eq(self.config, index, name, control)
        else:
            master = self.config[index[0]][index[1]]['name']
            self.pulse.remove_eq(self.config, master, name, index[0] + index[1], index)

    def rnnoise_toggle(self, widget, source_index, sink_name):
        stat = 'connect' if widget.get_active() == True else 'disconnect'
        self.pulse.rnnoise(self.config, source_index, sink_name, stat)

    def mute_toggle(self, button, index, device):
        state = 1 if button.get_active() else 0
        self.pulse.mute(self.config, index, device, state)

    def loopback_toggle(self, button, sink_index, source_index):
        state = "connect" if button.get_active() else "disconnect"
        self.pulse.connect(self.config, state, source_index, sink_index)

    def loopback_latency_popop(self, widget, event, index):
        if event.button == 3:
            Latency_Popup(widget, self.pulse, self.config, self.gladefile, index)

    def rnnoise_popop(self, widget, event, index):
        if event.button == 3:
            Rnnoise_Popup(widget, self.config, self.pulse, self.gladefile, index)

    def open_eq(self, button, event, index, name):
        if event.button == 3:
            if self.config[index[0]][index[1]]['name'] == '':
                return

            EqPopover(button, self.config, self.pulse, self.gladefile, index, name)

    def set_popup_entry(self, widget):
        name = widget.get_text()
        if self.pulse.rename(self.config, self.Label_Index, name) == True:
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
            self.config[index[0]][index[1]]['name'] = device[model - 1][0]
        else:
            self.config[index[0]][index[1]]['name'] = ""

    def delete_event(self, widget, event, donnees=None):
        with open(get_config_path(), 'w') as outfile:
            json.dump(self.config, outfile, indent='\t', separators=(',', ': '))
        Gtk.main_quit()
        return False

def get_config_path(glade=False):
    config_path = os.getenv('XDG_CONFIG_HOME')
    if config_path == None:
        config_path = os.getenv('HOME')
        config_path = os.path.join(config_path,'.config')
    config_path = os.path.join(config_path,'pulsemeeter')
    Path(config_path).mkdir(parents=True, exist_ok=True)
    config_file = os.path.join(config_path,'config.json')
    glade_file = os.path.join(config_path,'Interface.glade')
    if glade == True:
        return glade_file
    return config_file
