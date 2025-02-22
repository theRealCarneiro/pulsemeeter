from meexer.model.device_model import DeviceModel
from meexer.model.connection_model import ConnectionModel
from meexer.clients.gtk.widgets.common.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.common.mute_widget import MuteWidget
from meexer.clients.gtk.widgets.common.default_widget import DefaultWidget
from meexer.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from meexer.clients.gtk.widgets.common.icon_button_widget import IconButton
from meexer.clients.gtk.widgets.device.connection_box_widget import ConnectionBoxWidget
from meexer.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter
from meexer.clients.gtk.adapters.connection_box_adapter import ConnectionBoxAdapter

from meexer.clients.gtk.widgets.device.name_widget import NameWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceAdapter(GObject.GObject):
    device_model: DeviceModel
    name_widget: NameWidget
    volume_widget: VolumeWidget
    mute_widget: MuteWidget
    primary_widget: DefaultWidget
    vumeter_widget: VumeterWidget
    edit_button: IconButton
    popover: DeviceSettingsAdapter
    connections_widget: ConnectionBoxAdapter
    handlers: dict[str, int]

    __gsignals__ = {
        "mute": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "primary": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "volume": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        "remove_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        "connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool))
    }

    def __init__(self, model: DeviceModel):
        super().__init__()
        self.device_model = model

        self.edit_button.connect('pressed', self.edit_device_popover)

        self.handlers['volume'] = self.volume_widget.connect('value-changed', self.update_model_volume)
        self.handlers['mute'] = self.mute_widget.connect('toggled', self.update_model_mute)
        self.handlers['primary'] = self.primary_widget.connect('pressed', self.update_model_primary)
        self.handlers['remove_pressed'] = self.popover.remove_button.connect('pressed', self.update_model_remove)
        if model.get_type() in ('vi', 'hi'):
            self.handlers['connection'] = self.connections_widget.connect('connection', self.update_model_connection)

        # self.device_model.connect('connection', self.set)
        # self.device_model.connect('volume', self.set_volume)
        # self.device_model.connect('mute', self.set_mute)

    def edit_device_popover(self, _):
        self.popover.show_all()
        self.popover.popup()

    def insert_connection_widget(self, connection_schema: ConnectionModel, output_type: str, output_id: str):
        button = self.connections_widget.insert_widget(connection_schema, output_type, output_id)

        return button

    def remove_connection_widget(self, output_type, output_id):
        self.connections_widget.remove_button(output_type, output_id)

    def update_model_volume(self, volume_widget):
        volume = volume_widget.get_value()
        self.emit('volume', int(volume))

    def update_model_mute(self, mute_widget):
        state = mute_widget.get_active()
        self.emit('mute', state)

    def update_model_primary(self, primary_widget):
        # state = primary_widget.get_active()
        primary_widget.set_primary(True)
        self.emit('primary', True)

    def update_model_connection(self, button, device_type, device_id, state):
        # state = button.get_active()
        self.emit('connection', device_type, device_id, state)

    def update_model_remove(self, _):
        self.emit('remove_pressed', self.device_model.get_type())

    def set_volume(self, value):
        print('Setting widget volume')
        self.volume_widget.handler_block(self.handlers['volume'])
        self.volume_widget.set_value(value)
        self.volume_widget.handler_unblock(self.handlers['volume'])

    def set_mute(self, value):
        print('Setting widget mute')
        self.volume_widget.handler_block(self.handlers['mute'])
        self.volume_widget.set_value(value)
        self.volume_widget.handler_unblock(self.handlers['mute'])

    def set_primary(self, state):
        print(self.device_model.name, state)
        self.primary_widget.handler_block(self.handlers['primary'])
        self.primary_widget.set_primary(state)
        self.primary_widget.handler_unblock(self.handlers['primary'])
