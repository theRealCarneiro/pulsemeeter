import os
import sys
from .settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk

class PortSelectPopover():
    def __init__(self, button, pulse, index):

        self.config = pulse.config
        self.builder = Gtk.Builder()
        self.layout = pulse.config['layout']

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
                [
                    'portselect_popover',
                    'portselect_grouping_toggle',
                    'portselect_stack',
                    'portselect_grouped_ports',
                    'portselect_notebook',
                    'portselect_left_ports',
                    'portselect_right_ports',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.PortSelect_Popover = self.builder.get_object('portselect_popover')
        self.PortSelect_Popover.set_relative_to(button)

        self.Toggle_Grouping = self.builder.get_object('portselect_grouping_toggle')
        self.Toggle_Grouping.set_active(True)  # Set from config
        self.grouping = True  # Set from config
        self.Toggle_Grouping.connect('toggled', self.toggle_grouping, index, pulse)

        self.Grouped_Ports = self.builder.get_object('portselect_grouped_ports')
        self.PortSelect_Notebook = self.builder.get_object('portselect_notebook')
        self.Left_Ports = self.builder.get_object('portselect_left_ports')
        self.Right_Ports = self.builder.get_object('portselect_right_ports')

        self.PortSelect_Stack = self.builder.get_object('portselect_stack')
        self.PortSelect_Stack.set_visible_child(self.Grouped_Ports if self.grouping else self.PortSelect_Notebook)

        self.port_names = ['test 1', 'test 2', 'test 3', 'test 4', 'test 5'] # read from config here
        self.port_widget_handles = {'left': {}, 'right': {}, 'grouped': {}}
        for i in range(len(self.port_names)):
            self.add_port(self.port_names[i], index, pulse)
            if i % 2 == 1:
                self.add_grouped_port(self.port_names[i - 1], self.port_names[i], index, pulse)

        self.PortSelect_Popover.popup()

    def add_port(self, name, index, pulse):
        left_widget = Gtk.ToggleButton.new_with_label(name)
        right_widget = Gtk.ToggleButton.new_with_label(name)
        self.port_widget_handles['left'][name] =\
            [
                left_widget,
                left_widget.connect('toggled', self.toggle_port, 'left', name, index, pulse, True)
            ]
        self.port_widget_handles['right'][name] = \
            [
                right_widget,
                right_widget.connect('toggled', self.toggle_port, 'right', name, index, pulse, True)
            ]
        self.Left_Ports.add(left_widget)
        self.Right_Ports.add(right_widget)
        left_widget.show()
        right_widget.show()

    def add_grouped_port(self, left, right, index, pulse):
        name = f'{left}, {right}'
        widget = Gtk.ToggleButton.new_with_label(name)
        self.port_widget_handles['grouped'][name] =\
            [
                widget,
                [left, right],
                widget.connect('toggled', self.toggle_grouped_port, name, index, pulse)
            ]
        self.port_widget_handles['grouped'][left] = self.port_widget_handles['grouped'][name]
        self.port_widget_handles['grouped'][right] = self.port_widget_handles['grouped'][name]
        self.Grouped_Ports.add(widget)
        widget.show()

    def toggle_grouping(self, widget, index, pulse):
        self.grouping = self.Toggle_Grouping.get_active()
        # set config here
        self.PortSelect_Stack.set_visible_child(self.Grouped_Ports if self.grouping else self.PortSelect_Notebook)

    def toggle_port(self, widget, v_port, name, index, pulse, from_event):
        print(name, from_event)
        if from_event and name in self.port_widget_handles['grouped']:
            grouped_handle = self.port_widget_handles['grouped'][name]
            if self.port_widget_handles['left'][self.port_widget_handles['grouped'][name][1][0]][0].get_active() and\
                    self.port_widget_handles['right'][self.port_widget_handles['grouped'][name][1][1]][0].get_active():
                if not self.port_widget_handles['grouped'][name][0].get_active():
                    grouped_handle[0].handler_block(grouped_handle[2])
                    self.port_widget_handles['grouped'][name][0].set_active(True)
                    grouped_handle[0].handler_unblock(grouped_handle[2])
            elif self.port_widget_handles['grouped'][name][0].get_active():
                grouped_handle[0].handler_block(grouped_handle[2])
                self.port_widget_handles['grouped'][name][0].set_active(False)
                grouped_handle[0].handler_unblock(grouped_handle[2])
        # v_port will be either 'left' or 'right' (for future this could be a number for more than stereo)
        # name will be the name of the port to connect as given to the constructor
        # do whatever is necessary to connect or disconnect the port, and change the relevant setting in the config
        pass

    def toggle_grouped_port(self, widget, name, index, pulse):
        print(name)
        is_active = widget.get_active()
        ports = self.port_widget_handles['grouped'][name][1]
        handles = [
            self.port_widget_handles['left'][ports[0]],
            self.port_widget_handles['right'][ports[1]],
        ]
        if handles[0][0].get_active() != is_active:
            handles[0][0].handler_block(handles[0][1])
            handles[0][0].set_active(is_active)
            handles[0][0].handler_unblock(handles[0][1])
            self.toggle_port(handles[0][0], 'left', ports[0], index, pulse, False)
        if handles[1][0].get_active() != is_active:
            handles[1][0].handler_block(handles[1][1])
            handles[1][0].set_active(is_active)
            handles[1][0].handler_unblock(handles[1][1])
            self.toggle_port(handles[1][0], 'right', ports[1], index, pulse, False)
