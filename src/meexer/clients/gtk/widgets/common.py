# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


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

    def __init__(self, option_name: str, option_value=None):
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
                print(i)

    def insert_entry(self):
        pass

    def remove_entry(self):
        pass


class PortSelector(Gtk.Grid):
    '''
    Widget
    '''

    def __init__(self):
        super().__init__()
        self.label = Gtk.Label('Selected ports: ')
        self.port_grid = Gtk.Grid()
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.port_grid, 1, 0, 1, 1)
