# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class NameWidget(Gtk.HBox):

    def __init__(self, nick: str, description: str):
        super().__init__(spacing=1)
        self.description_label = None
        self.nick_label = Gtk.Label(halign=Gtk.Align.START)
        self.nick_label.set_markup(f'<b>{nick}</b>')
        self.pack_start(self.nick_label, False, False, 10)

        if description == nick:
            return

        self.description_label = Gtk.Label(halign=Gtk.Align.START)
        self.description_label.set_markup(f'<small>{description}</small>')
        self.pack_start(self.description_label, False, False, 10)

    @property
    def description(self) -> str:
        if self.description_label is None:
            return self.nick_label.get_text()

        return self.description_label.get_text()

    @property
    def nick(self) -> str:
        return self.nick_label.get_text()
