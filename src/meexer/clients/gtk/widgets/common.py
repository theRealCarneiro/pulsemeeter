# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


CHANNEL_MAPS = {
    "mono": ["mono"],
    "stereo": ["front-left", "front-right"],
    "quad": ["front-left", "front-right", "rear-left", "rear-right"],
    "5.0": ["front-left", "front-right", "front-center", "rear-left", "rear-right"],
    "5.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right"],
    "7.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right", "side-left", "side-right"]
}


class IconButton(Gtk.Button):
    '''
    A button with an icon
    '''

    def __init__(self, icon_name: str):
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image()
        image.set_from_gicon(icon, Gtk.IconSize.MENU)
        super().__init__()
        self.add(image)


class InputWidget(Gtk.Grid):
    '''
    Widget for a labeled input option
    '''

    def __init__(self, option_name: str, option_value=''):
        super().__init__()
        self.label = Gtk.Label(option_name)

        if option_name is None:
            option_value = ''

        self.input = Gtk.Entry(text=str(option_value), hexpand=True)
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.input, 1, 0, 1, 1)

    def get_option(self):
        return self.input.get_text()


class LabeledCombobox(Gtk.Grid):
    '''
    Widget for a labeled combobox
    '''

    def __init__(self, label, entries: list = None):
        super().__init__()
        self.label = Gtk.Label(label)
        self.combobox = Gtk.ComboBoxText(hexpand=True)
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.combobox, 1, 0, 1, 1)

        # insert in combobox
        if entries is not None:
            for i in entries:
                self.insert_entry(i)

    def insert_entry(self, entry):
        self.combobox.append_text(entry)

    def remove_entry(self):
        pass


class PortSelector(Gtk.Grid):
    '''
    Widget
    '''

    def __init__(self):
        super().__init__()
        self.label = Gtk.Label('Selected ports: ')
        # self.port_grid = Gtk.Grid()
        self.port_box = Gtk.HBox()
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.port_box, 1, 0, 1, 1)

    def set_ports(self, channel_map, selected_channels=None):
        for child in self.port_box.get_children():
            self.port_box.remove(child)

        # for port in channel_map:
        for port in range(len(channel_map)):
            enabled = selected_channels[port] if selected_channels is not None else True
            check = Gtk.CheckButton(label=port, active=enabled)
            self.port_box.pack_start(check, False, False, 0)

        self.port_box.show_all()

    def get_selected(self):
        selected_channels = []
        for child in self.port_box.get_children():
            selected_channels.append(True if child.get_active() else False)

        return selected_channels
