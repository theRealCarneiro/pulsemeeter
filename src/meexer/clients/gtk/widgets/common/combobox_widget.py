# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class LabeledCombobox(Gtk.Grid):
    '''
    Widget for a labeled combobox
    '''

    def __init__(self, label):
        super().__init__()
        self.label = Gtk.Label(label)
        self.combobox = Gtk.ComboBoxText(hexpand=True)
        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.combobox, 1, 0, 1, 1)

    def insert_entry(self, entry):
        self.combobox.append_text(entry)

    def load_list(self, entry_list, field=None):

        # insert entry itself
        if field is None:
            for entry in entry_list:
                self.insert_entry(entry)

        # entry is a dict, insert entry field
        else:
            for entry in entry_list:
                self.insert_entry(entry[field])

    def empty(self):
        self.combobox.remove_all()

    def get_active(self) -> int:
        self.combobox.get_active()

    def get_active_text(self) -> str:
        return self.combobox.get_active_text()

    def remove_entry(self):
        pass
