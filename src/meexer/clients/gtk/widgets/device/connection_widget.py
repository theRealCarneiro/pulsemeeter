from meexer.schemas.device_schema import ConnectionSchema

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class ConnectionWidget(Gtk.ToggleButton):

    def __init__(self, connection_schema: ConnectionSchema, output_type: str, output_id: str):
        super().__init__(label=connection_schema.nick, active=connection_schema.state)
        self.schema = connection_schema
        self.output_type = output_type
        self.output_id = output_id
