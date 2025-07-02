from pulsemeeter.clients.gtk.widgets.device.connection_widget import ConnectionWidget
from pulsemeeter.model.connection_model import ConnectionModel

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class ConnectionBoxAdapter(GObject.GObject):
    a: Gtk.Box
    b: Gtk.Box
    connection_widgets: dict[str, dict[str, ConnectionWidget]] = {'a': {}, 'b': {}}
    connections_schema: dict
    handlers: dict = {}
    model: dict[str, dict[str, ConnectionModel]]

    __gsignals__ = {
        "connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        "update_connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT))
    }

    def emit_connect_signal(self, widget, device_type, device_id):
        state = widget.get_active()
        # self.model[device_type][device_id].state = state
        self.emit('connection', device_type, device_id, state)

    def emit_update_signal(self, widget, device_type, device_id, button):
        popover = button.popover
        connection_model = popover.get_connection_model()
        self.emit('update_connection', device_type, device_id, connection_model)

    def refresh_connections(self):
        self.set_empty()
        self.load_widgets(self.model)

    def load_widgets(self, devices: dict[dict[str, ConnectionModel]]):
        for device_type in ('a', 'b'):
            for button_id, connection_schema in devices[device_type].items():
                self.insert_widget(connection_schema, device_type, button_id)

    def insert_widget(self, connection_schema: ConnectionModel, device_type, button_id: str):
        button = ConnectionWidget(connection_schema, device_type, button_id)
        self.connection_widgets[device_type][button_id] = button
        self.__dict__[device_type].pack_start(button, False, False, 0)

        # connect button to emit event connection event
        button.connect('toggled', self.emit_connect_signal, device_type, button_id)
        button.popover.confirm_button.connect('clicked', self.emit_update_signal, device_type, button_id, button)
        return button

    def remove_button(self, device_type, button_id):
        button = self.connection_widgets[device_type].pop(button_id)
        # self.__dict__[device_type].remove(button)
        button.destroy()

    def set_empty(self):
        for device_type in ('a', 'b'):
            for button in self.__dict__[device_type].get_children():
                self.__dict__[device_type].remove(button)
