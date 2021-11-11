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
                    'eq_popup',
                    'eq_50_hz_adjust',
                    'eq_100_hz_adjust',
                    'eq_156_hz_adjust',
                    'eq_220_hz_adjust',
                    'eq_311_hz_adjust',
                    'eq_440_hz_adjust',
                    'eq_622_hz_adjust',
                    'eq_880_hz_adjust',
                    'eq_1_25_khz_adjust',
                    'eq_1_75_khz_adjust',
                    'eq_2_5_khz_adjust',
                    'eq_3_5_khz_adjust',
                    'eq_5_khz_adjust',
                    'eq_10_khz_adjust',
                    'eq_20_khz_adjust',
                    'apply_eq_button',
                    'reset_eq_button',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        for i in range(1, 16):
            mark = self.builder.get_object(f'eq_{i}')
            mark.add_mark(0, Gtk.PositionType.TOP, '')

        self.eq = []
        self.eq.append(self.builder.get_object('eq_50_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_100_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_156_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_220_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_311_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_440_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_622_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_880_hz_adjust'))
        self.eq.append(self.builder.get_object('eq_1_25_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_1_75_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_2_5_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_3_5_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_5_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_10_khz_adjust'))
        self.eq.append(self.builder.get_object('eq_20_khz_adjust'))
        self.Apply_EQ_Button = self.builder.get_object('apply_eq_button')
        self.Reset_EQ_Button = self.builder.get_object('reset_eq_button')

        control = self.pulse.config[index[0]][index[1]]['eq_control'] 
        j = 0
        if control != '':
            for i in control.split(','):
                self.eq[j].set_value(float(i))
                j = j + 1

        self.Apply_EQ_Button.connect('pressed', self.apply_eq, index)
        self.Reset_EQ_Button.connect('pressed', self.reset_eq)

        self.EQ_Popup = self.builder.get_object('eq_popup')

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
