import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


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
        self.label.set_mnemonic_widget(self.input)
        self.input.get_accessible().set_name(option_name.strip(": "))
        self.input.set_tooltip_text(_("Enter the %s") % option_name.strip(': '))

        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.input, 1, 0, 1, 1)

    def get_option(self):
        return self.input.get_text()

    def set_option(self, option: str):
        self.input.set_text(option)
