import sys
from ..settings import GLADEFILE

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk,Gio

class AppList(Gtk.VBox):

    def __init__(self, dev_type, client):
        super().__init__(spacing=0)
        self.client = client
        self.config = client.config
        self.dev_type = dev_type

        self.box_list = []
        self.load_application_list()

    def load_application_list(self, id=None):
        if id == None and len(self.box_list) > 0:
            self.remove_app_dev()

        app_list = self.client.list_apps(self.dev_type)

        if len(app_list) == 0: 
            return

        name_vi = []
        name_b = []
        for i in ['vi', 'b']:
            for j in self.config[i]:
                device_config = self.config[i][j]
                if device_config['name'] != '':

                    # if virtual input
                    if i == 'vi':
                        name = device_config['name']
                        if self.dev_type == 'source-output':
                            name += '.monitor'
                        name_vi.append(name)

                    # if virtual output
                    elif self.dev_type != 'sink-input':
                        name_b.append(device_config['name'])

        if self.dev_type == 'source-output':
            name_b.extend(name_vi)
            dev_list = name_b
        else:
            dev_list = name_vi

        for i in app_list:
            if id != None:
                if str(id) != str(i['id']):
                    continue

            if 'icon' not in i:
                i['icon'] = 'audio-card'

            icon = Gio.ThemedIcon(name=i['icon'])
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
            image.set_margin_left(10)

            label = Gtk.Label(i['name'])
            label.props.halign = Gtk.Align.START

            combobox = Gtk.ComboBoxText()
            for dev in dev_list:
                combobox.append_text(dev)
            try:
                index = dev_list.index(i['device'])
            except:
                index = 0
            combobox.set_active(index)
            combobox.connect('changed', self.app_combo_change, i['id'])
            combobox.props.halign = Gtk.Align.END
            combobox.set_hexpand(True)
            combobox.set_margin_right(10)

            adjust = Gtk.Adjustment(lower=0, upper=153, step_increment=1, page_increment=10)
            adjust.set_value(self.client.get_app_volume(i['id'], self.dev_type))
            adjust.connect('value_changed', self.volume_change, i['id'], self.dev_type)

            scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjust)
            scale.set_hexpand(True)
            scale.set_value_pos(Gtk.PositionType.RIGHT)
            scale.set_digits(0)
            scale.add_mark(100, Gtk.PositionType.BOTTOM, '')
            scale.set_margin_left(10)

            separator_top = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator_top.set_margin_bottom(5)
            separator_bottom = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator_bottom.set_margin_top(5)

            box = Gtk.Box(spacing=5)
            box.pack_start(image, expand = False, fill = False, padding = 0)
            box.pack_start(label, expand = False, fill = False, padding = 0)
            box.pack_start(combobox, expand = False, fill = True, padding = 0)

            vbox = Gtk.VBox(spacing=0)
            vbox.pack_start(separator_top, expand = False, fill = False, padding = 0)
            vbox.pack_start(box, expand = False, fill = False, padding = 0)
            vbox.pack_start(scale, expand = False, fill = False, padding = 0)
            vbox.pack_start(separator_bottom, expand = False, fill = False, padding = 0)

            self.box_list.append([vbox, i['id']])
            self.pack_start(vbox, expand = False, fill = True, padding = 0)

            self.show_all()

    def remove_app_dev(self, id=None):
        if id == None:
            for i in self.box_list:
                self.remove(i[0])
            self.box_list.clear()
            return

        for i in self.box_list:
            if str(id) == str(i[1]):
                self.remove(i[0])
                self.box_list.remove(i)
                break

    def app_combo_change(self, combobox, app):
        name = combobox.get_active_text()
        self.client.move_app_device(app, name, self.dev_type)

    def volume_change(self, slider, index, stream_type=None):
        val = slider.get_value()
        self.client.set_app_volume(index, int(val), stream_type)
