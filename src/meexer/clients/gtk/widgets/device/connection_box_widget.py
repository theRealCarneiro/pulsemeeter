from meexer.clients.gtk.widgets.device.connection_widget import ConnectionWidget
from meexer.schemas.device_schema import ConnectionSchema

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class ConnectionBoxWidget(Gtk.Box):

    def __init__(self, output_type, connections_schemas: dict[str, ConnectionSchema]):
        super().__init__()
        self.output_type = output_type
        self.connection_widgets: dict[str, ConnectionWidget] = {}
        if connections_schemas is not None:
            self.load_widgets(connections_schemas)

    def load_widgets(self, devices: dict[str, ConnectionSchema]):
        for button_id, connection_schema in devices.items():
            self.insert_widget(connection_schema, button_id)

    def insert_widget(self, connection_schema: ConnectionSchema, button_id: str):
        button = ConnectionWidget(connection_schema, self.output_type, button_id)
        self.connection_widgets[button_id] = button
        self.pack_start(button, False, False, 0)
        return button

    # def insert_button(self, button: ConnectionWidget, button_id: str):
    #     self.connection_widgets[button_id] = button
    #     self.pack_start(button, False, False, 0)

    def remove_button(self, button_id):
        button = self.connection_widgets.pop(button_id)
        self.remove(button)
        button.destroy()
