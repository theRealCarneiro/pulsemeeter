import gettext
from pulsemeeter.schemas.device_schema import ConnectionSchema
from pulsemeeter.clients.gtk.widgets.device.edit_connection_widget import ConnectionSettingsPopup

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionWidget(Gtk.ToggleButton):

    def __init__(self, connection_schema: ConnectionSchema, output_type: str, output_id: str):
        super().__init__(label=connection_schema.nick, active=connection_schema.state)
        self.get_accessible().set_name(connection_schema.nick)
        self.schema = connection_schema
        self.output_type = output_type
        self.output_id = output_id
        self.popover = ConnectionSettingsPopup(connection_schema)
        self.popover.set_relative_to(self)
        self.connect('button-press-event', self.edit_settings_popover)

    def edit_settings_popover(self, _, event):
        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != 3:
            return

        self.popover.show_all()
        self.popover.popup()

