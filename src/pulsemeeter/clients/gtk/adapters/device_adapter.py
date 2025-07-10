import re

from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.device_manager_model import DeviceManagerModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget
from pulsemeeter.clients.gtk.widgets.common.mute_widget import MuteWidget
from pulsemeeter.clients.gtk.widgets.common.default_widget import DefaultWidget
from pulsemeeter.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.device.connection_box_widget import ConnectionBoxWidget
from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter
from pulsemeeter.clients.gtk.adapters.connection_box_adapter import ConnectionBoxAdapter

from pulsemeeter.clients.gtk.widgets.device.name_widget import NameWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, GLib  # noqa: E402
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
        "device_remove": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        "device_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        "update_connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT))
    }

    def __init__(self, model: DeviceModel):
        super().__init__()
        self.device_model = model

        self.edit_button.connect('clicked', self.edit_device_popover)

        self.handlers['device_change'] = self.popover.confirm_button.connect('clicked', self.update_model_settings)
        self.handlers['volume'] = self.volume_widget.connect('value-changed', self.update_model_volume)
        self.handlers['mute'] = self.mute_widget.connect('toggled', self.update_model_mute)
        self.handlers['primary'] = self.primary_widget.connect('clicked', self.update_model_primary)
        self.handlers['device_remove'] = self.popover.remove_button.connect('clicked', self.update_model_remove)
        if model.get_type() in ('vi', 'hi'):
            self.handlers['connection'] = self.connections_widget.connect('connection', self.update_model_connection)
            self.handlers['update_connection'] = self.connections_widget.connect('update_connection', self.update_model_connection_settings)

        # self.device_model.connect('connection', self.set)
        # self.device_model.connect('volume', self.set_volume)
        # self.device_model.connect('mute', self.set_mute)

    def edit_device_popover(self, _):
        self.popover.show_all()
        self.popover.fill_settings(self.device_model)
        self.popover.popup()
        device_type = self.device_model.get_type()
        if device_type in ('hi', 'a'):
            device_list = DeviceManagerModel.list_devices(device_type)
            self.popover.device_list = device_list
            self.popover.combobox_widget.empty()
            self.popover.combobox_widget.load_list(device_list, 'description', self.model.description)

        self.popover.nick_widget.input.grab_focus()

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

    def update_model_connection(self, _, device_type, device_id, state):
        # state = button.get_active()
        self.emit('connection', device_type, device_id, state)

    def update_model_connection_settings(self, _, device_type, device_id, connection_model):
        self.emit('update_connection', device_type, device_id, connection_model)

    def update_model_remove(self, _):
        self.emit('device_remove')

    def update_model_settings(self, _):
        schema = self.popover.to_schema()
        if len(schema['nick'].strip()) != 0 and re.match(r'^[a-zA-Z0-9_.\- ]+$', schema['nick']):
            self.emit('device_change', schema)
            self.popover.popdown()

    def device_update(self, device_model):
        self.name_widget.set_label(device_model.nick, device_model.description)

    def pa_device_change(self):
        vol = self.device_model.volume[0]
        mute = self.device_model.mute

        if self.volume_widget.blocked is False and vol != self.volume_widget.get_value():
            self.set_volume(vol)

        if self.mute_widget.get_active != mute:
            self.set_mute(mute)

    def set_volume(self, value):
        self.volume_widget.handler_block(self.handlers['volume'])
        self.volume_widget.set_value(value)
        self.volume_widget.handler_unblock(self.handlers['volume'])

    def set_mute(self, state):
        # print('Setting widget mute')
        self.mute_widget.handler_block(self.handlers['mute'])
        # GLib.idle_add(self.mute_widget.set_active, state)
        self.mute_widget.set_active(state)
        self.mute_widget.handler_unblock(self.handlers['mute'])

    def set_primary(self, state):
        # print(self.device_model.name, state)
        self.primary_widget.handler_block(self.handlers['primary'])
        self.primary_widget.set_primary(state)
        self.primary_widget.handler_unblock(self.handlers['primary'])
