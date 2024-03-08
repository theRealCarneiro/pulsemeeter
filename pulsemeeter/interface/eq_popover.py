import os
import sys
from ..settings import LAYOUT_DIR

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class EqPopover():

    def __init__(self, button, sock, output_type, output_id):

        self.builder = Gtk.Builder()
        self.sock = sock
        layout = sock.config['layout']
        self.device_config = sock.config[output_type][output_id]

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{layout}.glade'),
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
        self.apply_eq_button = self.builder.get_object('apply_eq_button')
        self.reset_eq_button = self.builder.get_object('reset_eq_button')

        control = self.device_config['eq_control'] 
        j = 0
        if control != '':
            for i in control.split(','):
                self.eq[j].set_value(float(i))
                j = j + 1

        self.apply_eq_button.connect('pressed', self.apply_eq, output_type, output_id)
        self.reset_eq_button.connect('pressed', self.reset_eq)

        self.eq_popover = self.builder.get_object('eq_popup')

        self.eq_popover.set_relative_to(button)
        self.eq_popover.popup()

        self.builder.connect_signals(self)

    def apply_eq(self, widget, output_type, output_id):
        # if self.device_config['use_eq'] == False:
            # return
        control=''
        for i in self.eq:
            control = control + ',' + str(i.get_value())
        control = control[1:]
        self.sock.eq(output_type, output_id, 'set', control=control)

    def reset_eq(self, widget):
        for i in self.eq:
            i.set_value(0)

    def reset_value(self, widget, event):
        if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 3:
            widget.set_value(0)
