# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

from pulsemeeter.clients.gtk.widgets.utils.widget_box import WidgetBox


class ConnectionContainer(WidgetBox):
    '''
    Specialized container for connection widgets.

    This container manages connection buttons and emits signals when
    connections are changed or updated.
    '''

    __gsignals__ = {
        'connection-changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        'connection-updated': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT)),
    }

    def __init__(self, device_type, orientation=Gtk.Orientation.HORIZONTAL, spacing=2, margin=0):
        super().__init__(orientation=orientation, spacing=spacing, margin=margin)
        self.device_type = device_type

    def add_connection_widget(self, device_id, connection_widget):
        '''
        Add a connection widget to the container.

        Args:
            device_id (str): ID of the device this connection represents
            connection_widget: The connection widget to add
        '''
        # Connect to the connection widget's signals
        connection_widget.connect('connection-changed', self._on_connection_changed, device_id)
        connection_widget.connect('connection-updated', self._on_connection_updated, device_id)

        # Add to the container
        self.add_widget(device_id, connection_widget)

    def update_connections(self, connection_models):
        '''
        Update the container with new connection models.

        Args:
            connection_models (dict): Dictionary of {device_id: connection_model}
        '''
        # Clear existing connections
        self.clear()

        # Add new connections
        for device_id, model in connection_models.items():
            # Create connection widget (this would be imported from your connection widget module)
            # connection_widget = ConnectionWidget(model, self.device_type, device_id)
            # self.add_connection_widget(device_id, connection_widget)
            pass  # Placeholder - you'll need to implement this

    def _on_connection_changed(self, widget, device_id, state):
        '''
        Handle connection state changes from child widgets.

        Args:
            widget: The connection widget that changed
            device_id (str): ID of the device
            state (bool): New connection state
        '''
        self.emit('connection-changed', self.device_type, device_id, state)

    def _on_connection_updated(self, widget, device_id, model):
        '''
        Handle connection model updates from child widgets.

        Args:
            widget: The connection widget that was updated
            device_id (str): ID of the device
            model: Updated connection model
        '''
        self.emit('connection-updated', self.device_type, device_id, model)

    # def get_connection_widget(self, device_id):
    #     '''
    #     Get a connection widget by device ID.
    #
    #     Args:
    #         device_id (str): ID of the device
    #
    #     Returns:
    #         ConnectionWidget: The connection widget, or None if not found
    #     '''
    #     return self.get_widget(device_id)
    #
    # def remove_connection_widget(self, device_id):
    #     '''
    #     Remove a connection widget by device ID.
    #
    #     Args:
    #         device_id (str): ID of the device
    #
    #     Returns:
    #         ConnectionWidget: The removed connection widget, or None if not found
    #     '''
    #     return self.remove_widget(device_id)
