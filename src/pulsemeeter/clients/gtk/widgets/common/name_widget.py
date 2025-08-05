import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class NameWidget(Gtk.Box):

    def __init__(self, nick: str, description: str):
        super().__init__(spacing=1)
        self.description_label = Gtk.Label(halign=Gtk.Align.START)
        self.nick_label = Gtk.Label(halign=Gtk.Align.START)
        self.nick_label.set_markup(f'<b>{nick}</b>')
        self.append(self.nick_label)
        self.append(self.description_label)

        if description != nick:
            self.description_label.set_markup(f'<small>{description}</small>')

    def set_label(self, nick, description=None):
        self.nick_label.set_text(nick)
        if description is not None and nick != description:
            self.description_label.set_text(description)

    @property
    def description(self) -> str:
        if self.description_label is None:
            return self.nick_label.get_text()

        return self.description_label.get_text()

    @property
    def nick(self) -> str:
        return self.nick_label.get_text()

    def get_full_name(self) -> str:
        nick = self.nick
        description = self.description
        if nick == description:
            return nick

        return f"{nick}, {description}"
