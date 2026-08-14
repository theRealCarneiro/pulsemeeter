# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class InputWidget(Gtk.Grid):
    '''
    Widget for a labeled input option
    '''

    def __init__(self, option_name: str, option_value='', tooltip=None):
        super().__init__()
        self.label = Gtk.Label(label=option_name)

        if option_name is None:
            option_value = ''

        self.input = Gtk.Entry(text=str(option_value), hexpand=True)
        self.input.set_accessible_role(Gtk.AccessibleRole.TEXT_BOX)
        self.label.set_mnemonic_widget(self.input)
        self.label.set_accessible_role(Gtk.AccessibleRole.LABEL)
        if tooltip is not None:
            self.input.set_tooltip_text(tooltip)

        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.input, 1, 0, 1, 1)

    def get_option(self):
        return self.input.get_text()

    def set_option(self, option: str):
        self.input.set_text(option)
