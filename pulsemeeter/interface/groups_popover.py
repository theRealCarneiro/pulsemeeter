import os
import re
import sys
from ..settings import LAYOUT_DIR
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')

from gi.repository import Gtk,Gdk,Gio

class JackGroupsPopover():
    def __init__(self, button, pulse):

        self.group_type = 'output_groups'
        self.config = pulse.config
        self.builder = Gtk.Builder()
        self.layout = pulse.config['layout']
        self.pulse = pulse

        try:
            self.builder.add_objects_from_file(
                os.path.join(LAYOUT_DIR, f'{self.layout}.glade'),
                [
                    'jack_group_popover',
                    'group_box',
                    'apply_groups_button',
                    'group_notebook',
                ]
            )
        except Exception as ex:
            print('Error building main window!\n{}'.format(ex))
            sys.exit(1)

        self.jack_group_popover = self.builder.get_object('jack_group_popover')
        self.jack_group_popover.set_relative_to(button)

        self.group_notebook = self.builder.get_object('group_notebook')
        self.group_notebook.connect('switch-page', self.change_notbook_page)

        self.group_entry = {
            'input_groups': self.builder.get_object('input_groups_name_entry'),
            'output_groups': self.builder.get_object('output_groups_name_entry')
        }

        self.create_button = {
            'input_groups': self.builder.get_object('create_input_groups_button'),
            'output_groups': self.builder.get_object('create_output_groups_button')
        }

        self.group_box = {
            'input_groups': self.builder.get_object('input_groups_box'),
            'output_groups': self.builder.get_object('output_groups_box')
        }

        for group_type in ['input_groups', 'output_groups']:
            self.create_button[group_type].connect('pressed', self.create_group, group_type)
        self.create_port_list()
        self.jack_group_popover.popup()

    def change_notbook_page(self, widget, evt, tmp):
        self.group_type = 'output_groups' if widget.get_current_page() == 1 else 'input_groups'

    def create_group(self, widget, group_type):
        name = self.group_entry[group_type].get_text()
        groups = self.pulse.config['jack'][group_type]
        if not re.match('^[a-zA-Z0-9]*$', name) or name in groups:
            return

        self.pulse.config['jack'][group_type][name] = []
        gbox = self.create_group_box(name, group_type)
        self.group_box[group_type].pack_start(gbox, True, True, 0)
        self.group_box[group_type].show_all()


    def create_port_list(self):
        ports = 4

        self.button_list = {'input_groups': {}, 'output_groups': {}}
        
        groups = self.pulse.config['jack'][self.group_type]
        for group_type in self.group_box:
            for group in self.group_box[group_type]:
                self.group_box[group_type].remove(group)

            for group in self.pulse.config['jack'][group_type]:
                gbox = self.create_group_box(group, group_type)
                self.group_box[group_type].pack_start(gbox, True, True, 0)

        self.group_box['input_groups'].show_all()
        self.group_box['output_groups'].show_all()

    def create_group_box(self, group, group_type):
        button_list = self.button_list[group_type]
        icon = Gio.ThemedIcon(name='edit-delete')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        button = Gtk.Button(image=image)
        button.connect('pressed', self.delete_group, group, group_type)
        ports = 4
        groups = self.pulse.config['jack'][group_type]
        hbox = Gtk.HBox(spacing=1)
        hbox.pack_start(button, False, True, 0)
        label = Gtk.Label(label=group)
        label.set_size_request(100,0)
        hbox.pack_start(label, True, True, 0)
        button_list[group] = {}
        for i in range(1, ports + 1):
            state = True if i in groups[group] else False
            button_list[group][i] = Gtk.CheckButton(label=i)
            button_list[group][i].set_active(state)
            button_list[group][i].connect('toggled', self.toggle_port, group, i)
            hbox.pack_start(button_list[group][i], True, True, 0)
        button_list[group]['widget'] = hbox
        return hbox

    def toggle_port(self, widget, group_name, port):
        if widget.get_active() == True:
            group = self.pulse.config['jack'][self.group_type][group_name]
            group.append(port)
            group.sort()
            self.pulse.config['jack'][self.group_type][group_name] = group
        else:
            self.pulse.config['jack'][self.group_type][group_name].remove(port)

    def delete_group(self, widget, group_name, group_type):
        del self.pulse.config['jack'][group_type][group_name]
        self.group_box[group_type].remove(self.button_list[group_type][group_name]['widget'])
        self.group_box[group_type].show_all()
