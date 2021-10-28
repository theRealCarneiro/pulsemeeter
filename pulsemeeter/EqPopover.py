import os
from .settings import GLADEFILE
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class EqPopover():

    def __init__(self, button, pulse, index):

        self.builder = Gtk.Builder()
        self.pulse = pulse

        try:
            self.builder.add_objects_from_file(
                GLADEFILE,
                [
                    'EQ_Popup',
                    'EQ_50_hz_Adjust',
                    'EQ_100_hz_Adjust',
                    'EQ_156_hz_Adjust',
                    'EQ_220_hz_Adjust',
                    'EQ_311_hz_Adjust',
                    'EQ_440_hz_Adjust',
                    'EQ_622_hz_Adjust',
                    'EQ_880_hz_Adjust',
                    'EQ_1_25_khz_Adjust',
                    'EQ_1_75_khz_Adjust',
                    'EQ_2_5_khz_Adjust',
                    'EQ_3_5_khz_Adjust',
                    'EQ_5_khz_Adjust',
                    'EQ_10_khz_Adjust',
                    'EQ_20_khz_Adjust',
                    'Apply_EQ_Button',
                    'Reset_EQ_Button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)


        self.eq = []
        self.eq.append(self.builder.get_object('EQ_50_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_100_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_156_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_220_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_311_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_440_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_622_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_880_hz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_1_25_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_1_75_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_2_5_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_3_5_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_5_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_10_khz_Adjust'))
        self.eq.append(self.builder.get_object('EQ_20_khz_Adjust'))
        self.Apply_EQ_Button = self.builder.get_object('Apply_EQ_Button')
        self.Reset_EQ_Button = self.builder.get_object('Reset_EQ_Button')

        control = self.pulse.config[index[0]][index[1]]['eq_control'] 
        j = 0
        if control != '':
            for i in control.split(','):
                self.eq[j].set_value(float(i))
                j = j + 1

        self.Apply_EQ_Button.connect('pressed', self.apply_eq, index)
        self.Reset_EQ_Button.connect('pressed', self.reset_eq)

        self.EQ_Popup = self.builder.get_object('EQ_Popup')

        self.EQ_Popup.set_relative_to(button)
        self.EQ_Popup.popup()

        self.builder.connect_signals(self)

    def apply_eq(self, widget, index):
        control=''
        for i in self.eq:
            control = control + ',' + str(i.get_value())
        control = control[1:]
        if self.pulse.config[index[0]][index[1]]['use_eq'] == False:
            return
        self.pulse.apply_eq(index, control=control)

    def disable_eq(self, widget, index):
        self.pulse.remove_eq(index)

    def reset_eq(self, widget):
        for i in self.eq:
            i.set_value(0)

    def reset_value(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            widget.set_value(0)

