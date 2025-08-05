import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class LabeledCombobox(Gtk.Grid):
    '''
    Widget for a labeled combobox
    '''

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, label):
        super().__init__()
        self.label = Gtk.Label(label=label)
        self.combobox = Gtk.ComboBoxText(hexpand=True)
        # self.combobox.get_accessible().set_name(label.strip(':'))
        self.combobox.set_tooltip_text(_('Select the %s') % label.strip(':'))
        self.label.set_mnemonic_widget(self.combobox)
        self.entry_list = None

        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.combobox, 1, 0, 1, 1)

        self._signal_handler_id = self.combobox.connect('changed', self._on_changed)

    def _on_changed(self, widget):
        active_text = self.get_active_text()
        self.emit('changed', active_text)

    def insert_entry(self, entry):
        self.combobox.append_text(entry)

    def load_list(self, entry_list, field=None, selected=None):
        self.entry_list = entry_list
        for entry in entry_list:
            self.insert_entry(entry if not field else entry.__dict__[field])

        if selected:
            self.set_active_name(selected)

    def set_active_name(self, item):
        model = self.combobox.get_model()
        for i, row in enumerate(model):
            if row[0] == item:
                self.set_active(i)

    def set_active(self, index):
        self.combobox.handler_block(self._signal_handler_id)
        self.combobox.set_active(index)
        self.combobox.handler_unblock(self._signal_handler_id)

    def empty(self):
        self.combobox.remove_all()

    def get_active_entry(self):
        active_index = self.get_active()
        return self.entry_list[active_index]

    def get_active_text(self) -> str:
        return self.combobox.get_active_text()

    def get_active(self) -> int:
        return self.combobox.get_active()

    def remove_entry(self):
        pass
