#!/usr/bin/env python3

import os
import sys
import subprocess
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk

class MainWindow(Gtk.Window):

    def __init__(self):
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
        self.Hardware_Input_1_Label.set_text(self.get_name('hi1','source'))
        self.Hardware_Input_1_Adjust = self.builder.get_object('Hardware_Input_1_Adjust')
        self.Hardware_Input_1_Adjust.connect('value-changed', self.slider_change, "source", "hi1")
        self.Hardware_Input_1_A1 = self.builder.get_object('Hardware_Input_1_A1')
        self.Hardware_Input_1_A2 = self.builder.get_object('Hardware_Input_1_A2')
        self.Hardware_Input_1_A3 = self.builder.get_object('Hardware_Input_1_A3')
        self.Hardware_Input_1_B1 = self.builder.get_object('Hardware_Input_1_B1')
        self.Hardware_Input_1_B2 = self.builder.get_object('Hardware_Input_1_B2')
        self.Hardware_Input_1_B3 = self.builder.get_object('Hardware_Input_1_B3')
        self.Hardware_Input_1_A1.connect("toggled", self.on_button_toggled, "a1", "hi1")
        self.Hardware_Input_1_A2.connect("toggled", self.on_button_toggled, "a2", "hi1")
        self.Hardware_Input_1_A3.connect("toggled", self.on_button_toggled, "a3", "hi1")
        self.Hardware_Input_1_B1.connect("toggled", self.on_button_toggled, "b1", "hi1", "", "\\\"_sink\\\"")
        self.Hardware_Input_1_B2.connect("toggled", self.on_button_toggled, "b2", "hi1", "", "\\\"_sink\\\"")
        self.Hardware_Input_1_B3.connect("toggled", self.on_button_toggled, "b3", "hi1", "", "\\\"_sink\\\"")

        self.Hardware_Input_2_Label = self.builder.get_object('Hardware_Input_2')
        self.Hardware_Input_2_Adjust = self.builder.get_object('Hardware_Input_2_Adjust')
        self.Hardware_Input_2_Adjust.connect('value-changed', self.slider_change, "source", "hi2")
        self.Hardware_Input_2_A1 = self.builder.get_object('Hardware_Input_2_A1')
        self.Hardware_Input_2_A2 = self.builder.get_object('Hardware_Input_2_A2')
        self.Hardware_Input_2_A3 = self.builder.get_object('Hardware_Input_2_A3')
        self.Hardware_Input_2_B1 = self.builder.get_object('Hardware_Input_2_B1')
        self.Hardware_Input_2_B2 = self.builder.get_object('Hardware_Input_2_B2')
        self.Hardware_Input_2_B3 = self.builder.get_object('Hardware_Input_2_B3')
        self.Hardware_Input_2_A1.connect("toggled", self.on_button_toggled, "a1", "hi2")
        self.Hardware_Input_2_A2.connect("toggled", self.on_button_toggled, "a2", "hi2")
        self.Hardware_Input_2_A3.connect("toggled", self.on_button_toggled, "a3", "hi2")
        self.Hardware_Input_2_B1.connect("toggled", self.on_button_toggled, "b1", "hi2", "", "\\\"_sink\\\"")
        self.Hardware_Input_2_B2.connect("toggled", self.on_button_toggled, "b2", "hi2", "", "\\\"_sink\\\"")
        self.Hardware_Input_2_B3.connect("toggled", self.on_button_toggled, "b3", "hi2", "", "\\\"_sink\\\"")

        self.Hardware_Input_3_Label = self.builder.get_object('Hardware_Input_3')
        self.Hardware_Input_3_Adjust = self.builder.get_object('Hardware_Input_3_Adjust')
        self.Hardware_Input_3_Adjust.connect('value-changed', self.slider_change, "source", "hi3")
        self.Hardware_Input_3_A1 = self.builder.get_object('Hardware_Input_3_A1')
        self.Hardware_Input_3_A2 = self.builder.get_object('Hardware_Input_3_A2')
        self.Hardware_Input_3_A3 = self.builder.get_object('Hardware_Input_3_A3')
        self.Hardware_Input_3_B1 = self.builder.get_object('Hardware_Input_3_B1')
        self.Hardware_Input_3_B2 = self.builder.get_object('Hardware_Input_3_B2')
        self.Hardware_Input_3_B3 = self.builder.get_object('Hardware_Input_3_B3')
        self.Hardware_Input_3_A1.connect("toggled", self.on_button_toggled, "a1", "hi3")
        self.Hardware_Input_3_A2.connect("toggled", self.on_button_toggled, "a2", "hi3")
        self.Hardware_Input_3_A3.connect("toggled", self.on_button_toggled, "a3", "hi3")
        self.Hardware_Input_3_B1.connect("toggled", self.on_button_toggled, "b1", "hi3", "", "\\\"_sink\\\"")
        self.Hardware_Input_3_B2.connect("toggled", self.on_button_toggled, "b2", "hi3", "", "\\\"_sink\\\"")
        self.Hardware_Input_3_B3.connect("toggled", self.on_button_toggled, "b3", "hi3", "", "\\\"_sink\\\"")

        self.Virtual_Input_1_Label = self.builder.get_object('Virtual_Input_1_Label')
        self.Virtual_Input_1_Label.set_text(self.get_name('vi1','sink'))
        self.Virtual_Input_1_Adjust = self.builder.get_object('Virtual_Input_1_Adjust')
        self.Virtual_Input_1_Adjust.connect('value-changed', self.slider_change, "sink", "vi1")
        self.Virtual_Input_1_A1 = self.builder.get_object('Virtual_Input_1_A1')
        self.Virtual_Input_1_A2 = self.builder.get_object('Virtual_Input_1_A2')
        self.Virtual_Input_1_A3 = self.builder.get_object('Virtual_Input_1_A3')
        self.Virtual_Input_1_B1 = self.builder.get_object('Virtual_Input_1_B1')
        self.Virtual_Input_1_B2 = self.builder.get_object('Virtual_Input_1_B2')
        self.Virtual_Input_1_B3 = self.builder.get_object('Virtual_Input_1_B3')
        self.Virtual_Input_1_A1.connect("toggled", self.on_button_toggled, "a1", "vi1", "\\\".monitor\\\"")
        self.Virtual_Input_1_A2.connect("toggled", self.on_button_toggled, "a2", "vi1", "\\\".monitor\\\"")
        self.Virtual_Input_1_A3.connect("toggled", self.on_button_toggled, "a3", "vi1", "\\\".monitor\\\"")
        self.Virtual_Input_1_B1.connect("toggled", self.on_button_toggled, "b1", "vi1", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_1_B2.connect("toggled", self.on_button_toggled, "b2", "vi1", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_1_B3.connect("toggled", self.on_button_toggled, "b3", "vi1", "\\\".monitor\\\"", "\\\"_sink\\\"")
        

        self.Virtual_Input_2_Label = self.builder.get_object('Virtual_Input_2_Label')
        self.Virtual_Input_2_Label.set_text(self.get_name('vi2','sink'))
        self.Virtual_Input_2_Adjust = self.builder.get_object('Virtual_Input_2_Adjust')
        self.Virtual_Input_2_Adjust.connect('value-changed', self.slider_change, "sink", "vi2")
        self.Virtual_Input_2_A1 = self.builder.get_object('Virtual_Input_2_A1')
        self.Virtual_Input_2_A2 = self.builder.get_object('Virtual_Input_2_A2')
        self.Virtual_Input_2_A3 = self.builder.get_object('Virtual_Input_2_A3')
        self.Virtual_Input_2_B1 = self.builder.get_object('Virtual_Input_2_B1')
        self.Virtual_Input_2_B2 = self.builder.get_object('Virtual_Input_2_B2')
        self.Virtual_Input_2_B3 = self.builder.get_object('Virtual_Input_2_B3')
        self.Virtual_Input_2_A1.connect("toggled", self.on_button_toggled, "a1", "vi2", "\\\".monitor\\\"")
        self.Virtual_Input_2_A2.connect("toggled", self.on_button_toggled, "a2", "vi2", "\\\".monitor\\\"")
        self.Virtual_Input_2_A3.connect("toggled", self.on_button_toggled, "a3", "vi2", "\\\".monitor\\\"")
        self.Virtual_Input_2_B1.connect("toggled", self.on_button_toggled, "b1", "vi2", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_2_B2.connect("toggled", self.on_button_toggled, "b2", "vi2", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_2_B3.connect("toggled", self.on_button_toggled, "b3", "vi2", "\\\".monitor\\\"", "\\\"_sink\\\"")

        self.Virtual_Input_3_Label = self.builder.get_object('Virtual_Input_3_Label')
        self.Virtual_Input_3_Label.set_text(self.get_name('vi3','sink'))
        self.Virtual_Input_3_Adjust = self.builder.get_object('Virtual_Input_3_Adjust')
        self.Virtual_Input_3_Adjust.connect('value-changed', self.slider_change, "sink", "vi3")
        self.Virtual_Input_3_A1 = self.builder.get_object('Virtual_Input_3_A1')
        self.Virtual_Input_3_A2 = self.builder.get_object('Virtual_Input_3_A2')
        self.Virtual_Input_3_A3 = self.builder.get_object('Virtual_Input_3_A3')
        self.Virtual_Input_3_B1 = self.builder.get_object('Virtual_Input_2_B1')
        self.Virtual_Input_3_B2 = self.builder.get_object('Virtual_Input_2_B2')
        self.Virtual_Input_3_B3 = self.builder.get_object('Virtual_Input_2_B3')
        self.Virtual_Input_3_A1.connect("toggled", self.on_button_toggled, "a1", "vi3", "\\\".monitor\\\"")
        self.Virtual_Input_3_A2.connect("toggled", self.on_button_toggled, "a2", "vi3", "\\\".monitor\\\"")
        self.Virtual_Input_3_A3.connect("toggled", self.on_button_toggled, "a3", "vi3", "\\\".monitor\\\"")
        self.Virtual_Input_3_B1.connect("toggled", self.on_button_toggled, "b1", "vi3", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_3_B2.connect("toggled", self.on_button_toggled, "b2", "vi3", "\\\".monitor\\\"", "\\\"_sink\\\"")
        self.Virtual_Input_3_B3.connect("toggled", self.on_button_toggled, "b3", "vi3", "\\\".monitor\\\"", "\\\"_sink\\\"")

        self.Master_A1_Adjust = self.builder.get_object('Master_A1_Adjust')
        self.Master_A1_Adjust.connect('value-changed', self.slider_change, "sink", "a1")

        self.Master_A2_Adjust = self.builder.get_object('Master_A2_Adjust')
        self.Master_A2_Adjust.connect('value-changed', self.slider_change, "sink", "a2")

        self.Master_A3_Adjust = self.builder.get_object('Master_A3_Adjust')
        self.Master_A3_Adjust.connect('value-changed', self.slider_change, "sink", "a3")

        self.Master_B1_Adjust = self.builder.get_object('Master_B1_Adjust')
        self.Master_B1_Adjust.connect('value-changed', self.slider_change, "source", "b1")

        self.Master_B2_Adjust = self.builder.get_object('Master_B2_Adjust')
        self.Master_B2_Adjust.connect('value-changed', self.slider_change, "source", "b2")

        self.Master_B3_Adjust = self.builder.get_object('Master_B3_Adjust')
        self.Master_B3_Adjust.connect('value-changed', self.slider_change, "source", "b3")


        self.Window = self.builder.get_object('Window')

        self.Window.connect("delete_event", self.delete_event)

        self.builder.connect_signals(self)
        self.Window.show_all()

    def slider_change(self, slider, name, sink):
        val = slider.get_value()
        command = "/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh volume " + name + " " + sink + " " + str(int(val))
        print(command)
        os.popen(command)

    def on_button_toggled(self, button, source, sink, sink_sufix='', source_sufix=''):
        if button.get_active():
            # command = "/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh connect " + sink + " " + source + " " + op
            command = "/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh connect " + sink + sink_sufix + " " + source + source_sufix
            print(command)
            os.popen(command)
        else:
            # command = "/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh disconnect " + sink + " " + source + " " + op
            command = "/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh disconnect " + sink + sink_sufix + " " + source + source_sufix
            print(command)
            os.popen(command)

    def delete_event(self, widget, event, donnees=None):
        Gtk.main_quit()
        return False

    def get_name(self, name, sink=''):
        sys.stdout.flush()
        MyOut = subprocess.Popen(['/home/gabriel/Bibliotecas/Projects/pulsemeeter/pulsemeeter.sh','get', sink, name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
        stdout,stderr = MyOut.communicate()
        return stdout.decode()


def main():
    app = MainWindow()  # noqa
    return Gtk.main()


if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
