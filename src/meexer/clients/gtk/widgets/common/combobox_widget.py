# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


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

    def get_active(self, entry):
        self.combobox.get_active()

    def remove_entry(self):
        pass

