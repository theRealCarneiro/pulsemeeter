import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class LabeledDropDown(Gtk.Grid):
    '''
    Widget for a labeled dropdown
    '''

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, label):
        super().__init__()
        self.label = Gtk.Label(label=label)
        self.string_list = Gtk.StringList()
        self.dropdown = Gtk.DropDown(model=self.string_list, hexpand=True)
        self.dropdown.set_tooltip_text(_('Select the %s') % label.strip(':'))
        self.label.set_mnemonic_widget(self.dropdown)
        self.entry_list = None

        self.attach(self.label, 0, 0, 1, 1)
        self.attach(self.dropdown, 1, 0, 1, 1)

        self._signal_handler_id = self.dropdown.connect('notify::selected', self._on_selected)

    def disable_dropdown_autohide(self):
        internal_popover = self.dropdown.get_last_child()
        if isinstance(internal_popover, Gtk.Popover):
            internal_popover.set_autohide(False)

    def _on_selected(self, widget, pspec):
        active_text = self.get_active_text()
        if active_text is not None:
            self.emit('changed', active_text)

    def insert_entry(self, entry):
        self.string_list.append(entry)

    def load_list(self, entry_list, field=None, selected=None):
        self.entry_list = entry_list
        self.string_list.splice(0, self.string_list.get_n_items(), [])
        for entry in entry_list:
            self.insert_entry(entry if not field else entry.__dict__[field])

        if selected:
            self.set_active_name(selected)

    def set_active_name(self, item):
        for i in range(self.string_list.get_n_items()):
            if self.string_list.get_string(i) == item:
                self.set_active(i)
                return

    def set_active(self, index):
        self.dropdown.handler_block(self._signal_handler_id)
        self.dropdown.set_selected(index)
        self.dropdown.handler_unblock(self._signal_handler_id)

    def empty(self):
        self.string_list.splice(0, self.string_list.get_n_items(), [])

    def get_active_entry(self):
        active_index = self.get_active()
        if active_index == Gtk.INVALID_LIST_POSITION or self.entry_list is None:
            return None
        return self.entry_list[active_index]

    def get_active_text(self) -> str:
        index = self.get_active()
        if index == Gtk.INVALID_LIST_POSITION:
            return None
        return self.string_list.get_string(index)

    def get_active(self) -> int:
        return self.dropdown.get_selected()

    def remove_entry(self):
        pass
