import os
import json
import sys
import subprocess
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk

class MainWindow(Gtk.Window):

    def __init__(self, config):
        self.config = config
        Gtk.Window.__init__(self)
        self.builder = Gtk.Builder()
        gladefile = '/home/gabriel/Bibliotecas/Projects/pulsemeeter/Interface.glade'
        if not os.path.exists(gladefile):
            gladefile = os.path.join(sys.path[0], gladefile)

        try:
            self.builder.add_objects_from_file(
                gladefile,
                [
                    'A2_Button',
                    'A3_Butto',
                    'A3_Button',
                    'Hardware_Input_1_Label',
                    'Hardware_Input_1_Adjust',
                    'Hardware_Input_1_A1',
                    'Hardware_Input_1_A2',
                    'Hardware_Input_1_A3',
                    'Hardware_Input_1_B1',
                    'Hardware_Input_1_B2',
                    'Hardware_Input_1_B3',

                    'Hardware_Input_2_Label',
                    'Hardware_Input_2_Adjust',
                    'Hardware_Input_2_A1',
                    'Hardware_Input_2_A2',
                    'Hardware_Input_2_A3',
                    'Hardware_Input_2_B1',
                    'Hardware_Input_2_B2',
                    'Hardware_Input_2_B3',

                    'Hardware_Input_3_Label',
                    'Hardware_Input_3_Adjust',
                    'Hardware_Input_3_A1',
                    'Hardware_Input_3_A2',
                    'Hardware_Input_3_A3',
                    'Hardware_Input_3_B1',
                    'Hardware_Input_3_B2',
                    'Hardware_Input_3_B3',

                    'Virtual_Input_1_Label',
                    'Virtual_Input_1_Adjust',
                    'Virtual_Input_1_A1',
                    'Virtual_Input_1_A2',
                    'Virtual_Input_1_A3',
                    'Virtual_Input_1_B1',
                    'Virtual_Input_1_B2',
                    'Virtual_Input_1_B3',

                    'Virtual_Input_2_Label',
                    'Virtual_Input_2_Adjust',
                    'Virtual_Input_2_A1',
                    'Virtual_Input_2_A2',
                    'Virtual_Input_2_A3',
                    'Virtual_Input_2_B1',
                    'Virtual_Input_2_B2',
                    'Virtual_Input_2_B3',

                    'Virtual_Input_3_Label',
                    'Virtual_Input_3_Adjust',
                    'Virtual_Input_3_A1',
                    'Virtual_Input_3_A2',
                    'Virtual_Input_3_A3',
                    'Virtual_Input_3_B1',
                    'Virtual_Input_3_B2',
                    'Virtual_Input_3_B3',

                    'Master_A1_Adjust',
                    'Master_A2_Adjust',
                    'Master_A3_Adjust',
                    'Master_B1_Adjust',
                    'Master_B2_Adjust',
                    'Master_B3_Adjust',
                    'Window',
                ]
            )
        except Exception as ex:
            print('\\nError building main window!\\n{}'.format(ex))
            sys.exit(1)

        self.A2_Button = self.builder.get_object('A2_Button')
        self.A3_Butto = self.builder.get_object('A3_Butto')
        self.A3_Button = self.builder.get_object('A3_Button')

        self.Hardware_Input_1_Label = self.builder.get_object('Hardware_Input_1_Label')
        # self.Hardware_Input_1_Label.set_text(self.get_name('hi1','src'))
        self.Hardware_Input_1_Adjust = self.builder.get_object('Hardware_Input_1_Adjust')
        self.Hardware_Input_1_Adjust.set_value(self.config['hi']['1']['vol'])
        self.Hardware_Input_1_Adjust.connect('value-changed', self.slider_change, "source", self.config['hi']['1']['name'], ['vol','hi','1'])
        self.Hardware_Input_1_A1 = self.builder.get_object('Hardware_Input_1_A1')
        self.Hardware_Input_1_A2 = self.builder.get_object('Hardware_Input_1_A2')
        self.Hardware_Input_1_A3 = self.builder.get_object('Hardware_Input_1_A3')
        self.Hardware_Input_1_B1 = self.builder.get_object('Hardware_Input_1_B1')
        self.Hardware_Input_1_B2 = self.builder.get_object('Hardware_Input_1_B2')
        self.Hardware_Input_1_B3 = self.builder.get_object('Hardware_Input_1_B3')

        self.Hardware_Input_1_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['hi']['1']['name'], ['a1','hi','1'])
        self.Hardware_Input_1_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['hi']['1']['name'], ['a2','hi','1'])
        self.Hardware_Input_1_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['hi']['1']['name'], ['a3','hi','1'])
        self.Hardware_Input_1_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['hi']['1']['name'], ['b1','hi','1'], "", "_sink")
        self.Hardware_Input_1_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['hi']['1']['name'], ['b2','hi','1'], "", "_sink")
        self.Hardware_Input_1_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['hi']['1']['name'], ['b3','hi','1'], "", "_sink")

        self.Hardware_Input_2_Label = self.builder.get_object('Hardware_Input_2')
        self.Hardware_Input_2_Adjust = self.builder.get_object('Hardware_Input_2_Adjust')
        self.Hardware_Input_2_Adjust.set_value(self.config['hi']['2']['vol'])
        self.Hardware_Input_2_Adjust.connect('value-changed', self.slider_change, "source", self.config['hi']['2']['name'], ['vol','hi','2'])
        self.Hardware_Input_2_A1 = self.builder.get_object('Hardware_Input_2_A1')
        self.Hardware_Input_2_A2 = self.builder.get_object('Hardware_Input_2_A2')
        self.Hardware_Input_2_A3 = self.builder.get_object('Hardware_Input_2_A3')
        self.Hardware_Input_2_B1 = self.builder.get_object('Hardware_Input_2_B1')
        self.Hardware_Input_2_B2 = self.builder.get_object('Hardware_Input_2_B2')
        self.Hardware_Input_2_B3 = self.builder.get_object('Hardware_Input_2_B3')
        self.Hardware_Input_2_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['hi']['2']['name'], ['a1','hi','2'])
        self.Hardware_Input_2_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['hi']['2']['name'], ['a2','hi','2'])
        self.Hardware_Input_2_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['hi']['2']['name'], ['a3','hi','2'])
        self.Hardware_Input_2_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['hi']['2']['name'], ['b1','hi','2'], "", "_sink")
        self.Hardware_Input_2_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['hi']['2']['name'], ['b2','hi','2'], "", "_sink")
        self.Hardware_Input_2_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['hi']['2']['name'], ['b3','hi','2'], "", "_sink")

        self.Hardware_Input_3_Label = self.builder.get_object('Hardware_Input_3')
        self.Hardware_Input_3_Adjust = self.builder.get_object('Hardware_Input_3_Adjust')
        self.Hardware_Input_3_Adjust.set_value(self.config['hi']['3']['vol'])
        self.Hardware_Input_3_Adjust.connect('value-changed', self.slider_change, "source", self.config['hi']['3']['name'], ['vol','hi','3'])
        self.Hardware_Input_3_A1 = self.builder.get_object('Hardware_Input_3_A1')
        self.Hardware_Input_3_A2 = self.builder.get_object('Hardware_Input_3_A2')
        self.Hardware_Input_3_A3 = self.builder.get_object('Hardware_Input_3_A3')
        self.Hardware_Input_3_B1 = self.builder.get_object('Hardware_Input_3_B1')
        self.Hardware_Input_3_B2 = self.builder.get_object('Hardware_Input_3_B2')
        self.Hardware_Input_3_B3 = self.builder.get_object('Hardware_Input_3_B3')
        self.Hardware_Input_3_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['hi']['3']['name'], ['a1','hi','3'])
        self.Hardware_Input_3_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['hi']['3']['name'], ['a2','hi','3'])
        self.Hardware_Input_3_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['hi']['3']['name'], ['a3','hi','3'])
        self.Hardware_Input_3_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['hi']['3']['name'], ['b1','hi','3'], "", "_sink")
        self.Hardware_Input_3_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['hi']['3']['name'], ['b2','hi','3'], "", "_sink")
        self.Hardware_Input_3_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['hi']['3']['name'], ['b3','hi','3'], "", "_sink")

        self.Virtual_Input_1_Label = self.builder.get_object('Virtual_Input_1_Label')
        # self.Virtual_Input_1_Label.set_text(self.get_name('vi1','virtual_sink'))
        self.Virtual_Input_1_Adjust = self.builder.get_object('Virtual_Input_1_Adjust')
        self.Virtual_Input_1_Adjust.set_value(self.config['vi']['1']['vol'])
        self.Virtual_Input_1_Adjust.connect('value-changed', self.slider_change, "sink", self.config['vi']['1']['name'], ['vol','vi','1'])
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
        self.Virtual_Input_1_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['vi']['1']['name'], ['a1','vi','1'], ".monitor")
        self.Virtual_Input_1_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['vi']['1']['name'], ['a2','vi','1'], ".monitor")
        self.Virtual_Input_1_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['vi']['1']['name'], ['a3','vi','1'], ".monitor")
        self.Virtual_Input_1_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['vi']['1']['name'], ['b1','vi','1'], ".monitor", "_sink")
        self.Virtual_Input_1_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['vi']['1']['name'], ['b2','vi','1'], ".monitor", "_sink")
        self.Virtual_Input_1_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['vi']['1']['name'], ['b3','vi','1'], ".monitor", "_sink")
        

        self.Virtual_Input_2_Label = self.builder.get_object('Virtual_Input_2_Label')
        # self.Virtual_Input_2_Label.set_text(self.get_name('vi2','virtual_sink'))
        self.Virtual_Input_2_Adjust = self.builder.get_object('Virtual_Input_2_Adjust')
        self.Virtual_Input_2_Adjust.set_value(self.config['vi']['2']['vol'])
        self.Virtual_Input_2_Adjust.connect('value-changed', self.slider_change, "sink", self.config['vi']['2']['name'], ['vol','vi','2'])
        self.Virtual_Input_2_A1 = self.builder.get_object('Virtual_Input_2_A1')
        self.Virtual_Input_2_A2 = self.builder.get_object('Virtual_Input_2_A2')
        self.Virtual_Input_2_A3 = self.builder.get_object('Virtual_Input_2_A3')
        self.Virtual_Input_2_B1 = self.builder.get_object('Virtual_Input_2_B1')
        self.Virtual_Input_2_B2 = self.builder.get_object('Virtual_Input_2_B2')
        self.Virtual_Input_2_B3 = self.builder.get_object('Virtual_Input_2_B3')
        self.Virtual_Input_2_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['vi']['2']['name'], ['a1','vi','2'], ".monitor", )
        self.Virtual_Input_2_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['vi']['2']['name'], ['a2','vi','2'], ".monitor", )
        self.Virtual_Input_2_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['vi']['2']['name'], ['a3','vi','2'], ".monitor", )
        self.Virtual_Input_2_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['vi']['2']['name'], ['b1','vi','2'], ".monitor", "_sink")
        self.Virtual_Input_2_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['vi']['2']['name'], ['b2','vi','2'], ".monitor", "_sink")
        self.Virtual_Input_2_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['vi']['2']['name'], ['b3','vi','2'], ".monitor", "_sink")
        self.Virtual_Input_2_A1.set_active(self.config['vi']['2']['a1'])
        self.Virtual_Input_2_A2.set_active(self.config['vi']['2']['a2'])
        self.Virtual_Input_2_A3.set_active(self.config['vi']['2']['a3'])
        self.Virtual_Input_2_B1.set_active(self.config['vi']['2']['b1'])
        self.Virtual_Input_2_B2.set_active(self.config['vi']['2']['b2'])
        self.Virtual_Input_2_B3.set_active(self.config['vi']['2']['b3'])

        self.Virtual_Input_3_Label = self.builder.get_object('Virtual_Input_3_Label')
        # self.Virtual_Input_3_Label.set_text(self.get_name('vi3','virtual_sink'))
        self.Virtual_Input_3_Adjust = self.builder.get_object('Virtual_Input_3_Adjust')
        self.Virtual_Input_3_Adjust.set_value(self.config['vi']['3']['vol'])
        self.Virtual_Input_3_Adjust.connect('value-changed', self.slider_change, "sink", self.config['vi']['3']['name'], ['vol','vi','3'])
        self.Virtual_Input_3_A1 = self.builder.get_object('Virtual_Input_3_A1')
        self.Virtual_Input_3_A2 = self.builder.get_object('Virtual_Input_3_A2')
        self.Virtual_Input_3_A3 = self.builder.get_object('Virtual_Input_3_A3')
        self.Virtual_Input_3_B1 = self.builder.get_object('Virtual_Input_3_B1')
        self.Virtual_Input_3_B2 = self.builder.get_object('Virtual_Input_3_B2')
        self.Virtual_Input_3_B3 = self.builder.get_object('Virtual_Input_3_B3')
        self.Virtual_Input_3_A1.connect("toggled", self.on_button_toggled, self.config['a']['1']['name'], config['vi']['3']['name'], ['a1','vi','3'], ".monitor")
        self.Virtual_Input_3_A2.connect("toggled", self.on_button_toggled, self.config['a']['2']['name'], config['vi']['3']['name'], ['a2','vi','3'], ".monitor")
        self.Virtual_Input_3_A3.connect("toggled", self.on_button_toggled, self.config['a']['3']['name'], config['vi']['3']['name'], ['a3','vi','3'], ".monitor")
        self.Virtual_Input_3_B1.connect("toggled", self.on_button_toggled, self.config['b']['1']['name'], config['vi']['3']['name'], ['b1','vi','3'], ".monitor", "_sink")
        self.Virtual_Input_3_B2.connect("toggled", self.on_button_toggled, self.config['b']['2']['name'], config['vi']['3']['name'], ['b2','vi','3'], ".monitor", "_sink")
        self.Virtual_Input_3_B3.connect("toggled", self.on_button_toggled, self.config['b']['3']['name'], config['vi']['3']['name'], ['b3','vi','3'], ".monitor", "_sink")
        self.Virtual_Input_3_A1.set_active(self.config['vi']['3']['a1'])
        self.Virtual_Input_3_A2.set_active(self.config['vi']['3']['a2'])
        self.Virtual_Input_3_A3.set_active(self.config['vi']['3']['a3'])
        self.Virtual_Input_3_B1.set_active(self.config['vi']['3']['b1'])
        self.Virtual_Input_3_B2.set_active(self.config['vi']['3']['b2'])
        self.Virtual_Input_3_B3.set_active(self.config['vi']['3']['b3'])

        self.Master_A1_Adjust = self.builder.get_object('Master_A1_Adjust')
        self.Master_A1_Adjust.set_value(self.config['a']['1']['vol'])
        self.Master_A1_Adjust.connect('value-changed', self.slider_change, "sink", self.config['a']['1']['name'], ['vol','a','1'])

        self.Master_A2_Adjust = self.builder.get_object('Master_A2_Adjust')
        self.Master_A2_Adjust.set_value(self.config['a']['2']['vol'])
        self.Master_A2_Adjust.connect('value-changed', self.slider_change, "sink", self.config['a']['2']['name'], ['vol','a','2'])

        self.Master_A3_Adjust = self.builder.get_object('Master_A3_Adjust')
        self.Master_A3_Adjust.set_value(self.config['a']['3']['vol'])
        self.Master_A3_Adjust.connect('value-changed', self.slider_change, "sink", self.config['a']['3']['name'], ['vol','a','3'])

        self.Master_B1_Adjust = self.builder.get_object('Master_B1_Adjust')
        self.Master_B1_Adjust.set_value(self.config['b']['1']['vol'])
        self.Master_B1_Adjust.connect('value-changed', self.slider_change, "source", self.config['b']['1']['name'], ['vol','b','1'])

        self.Master_B2_Adjust = self.builder.get_object('Master_B2_Adjust')
        self.Master_B2_Adjust.set_value(self.config['b']['2']['vol'])
        self.Master_B2_Adjust.connect('value-changed', self.slider_change, "source", self.config['b']['2']['name'], ['vol','b','2'])

        self.Master_B3_Adjust = self.builder.get_object('Master_B3_Adjust')
        self.Master_B3_Adjust.set_value(self.config['b']['3']['vol'])
        self.Master_B3_Adjust.connect('value-changed', self.slider_change, "source", self.config['b']['3']['name'], ['vol','b','3'])


        self.Window = self.builder.get_object('Window')

        self.Window.connect("delete_event", self.delete_event, self.config)

        self.builder.connect_signals(self)
        self.Window.show_all()

    def slider_change(self, slider, name, sink, index):
        val = int(slider.get_value())
        self.config[index[1]][index[2]][index[0]] = val
        if (name == '' or sink == ''):
            return
        command = f"/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh volume {name} {sink} {val}"
        print(command)
        os.popen(command)

    def on_button_toggled(self, button, source, sink, index, sink_sufix='', source_sufix=''):
        self.config[index[1]][index[2]][index[0]] = button.get_active()
        print(self.config[index[1]][index[2]][index[0]])
        if (source == '' or sink == ''):
            return
        state = "connect" if button.get_active() else "disconnect"
        command = f"/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh {state} {sink}{sink_sufix} {source}{source_sufix}"
        print(command)
        os.popen(command)

    def delete_event(self, widget, event, donnees=None):
        with open('config.json', 'w') as outfile:
            json.dump(self.config, outfile, indent='\t', separators=(',', ': '))
        Gtk.main_quit()
        return False
