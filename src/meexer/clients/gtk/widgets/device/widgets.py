from meexer.schemas.device_schema import DeviceSchema
from meexer.clients.gtk.widgets.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.mute_widget import MuteWidget
from meexer.clients.gtk.widgets.default_widget import DefaultWidget
from meexer.clients.gtk.widgets.vumeter_widget import VumeterWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class NameWidget(Gtk.VBox):

    def __init__(self, nick: str, name: str):
        super().__init__()
        self.name_label = None
        self.nick_label = Gtk.Label(label=nick)
        self.pack_start(nick, False, False, 10)

        if name == nick:
            return

        self.name_label = Gtk.Label(label=name)
        self.pack_start(self.name_label, False, False, 10)

    @property
    def name(self) -> str:
        if self.name_label is None:
            return self.nick_label.get_text()

        return self.name_label.get_text()

    @property
    def nick(self) -> str:
        if self.name_label is None:
            return self.nick_label.get_text()

        return self.name_label.get_text()
