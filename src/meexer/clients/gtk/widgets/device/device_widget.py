from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema
# from meexer.clients.gtk.widgets.common
from meexer.clients.gtk.widgets.common.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.common.mute_widget import MuteWidget
from meexer.clients.gtk.widgets.common.default_widget import DefaultWidget
from meexer.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from meexer.clients.gtk.widgets.common.icon_button_widget import IconButton

from meexer.clients.gtk.widgets.device.connection_widget import ConnectionWidget
# from meexer.clients.gtk.widgets.common.create_device_widget import CreateDevice

from meexer.clients.gtk.widgets.device.name_widget import NameWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceWidget(Gtk.Frame):

    def __init__(self, schema: DeviceSchema, device_id: str):
        super().__init__()
        self.schema = schema
        self.device_id = device_id

        # create containers
        main_grid = Gtk.Grid(margin=5, hexpand=True)
        info_grid = Gtk.Grid(margin_start=5, hexpand=True)
        connection_grid = Gtk.Grid(hexpand=True)
        control_grid = Gtk.Grid(hexpand=True)
        self.connections_box = {'a': Gtk.Box(), 'b': Gtk.Box()}

        edit_button = IconButton('edit')
        edit_button.set_halign(Gtk.Align.END)
        # edit_button.set_valign(Gtk.Align.START)
        self.edit_button = edit_button

        # self.edit_device_widget = CreateDevice(device_type, device_list)
        self.name_widget = NameWidget(schema.nick, schema.description)
        self.volume_widget = VolumeWidget(schema.volume[0])
        self.mute_widget = MuteWidget(state=schema.mute)
        self.vumeter_widget = VumeterWidget()

        # if schema.primary is not None:
        self.primary_widget = DefaultWidget(state=schema.primary)

        # create connection buttons
        self.connection_buttons = {'a': {}, 'b': {}}
        for output_type, outputs in schema.connections.items():
            for output_id, connection_schema in outputs.items():
                self.insert_connection_widget(output_type, output_id, connection_schema)

        # atatch widgets to containers
        info_grid.attach(self.name_widget, 0, 0, 1, 1)
        info_grid.attach(Gtk.HBox(hexpand=True, halign=Gtk.Align.FILL), 2, 0, 1, 1)
        info_grid.attach(self.edit_button, 2, 0, 1, 1)
        connection_grid.attach(self.connections_box['a'], 0, 0, 1, 1)
        connection_grid.attach(self.connections_box['b'], 1, 0, 1, 1)
        control_grid.attach(self.volume_widget, 0, 0, 1, 1)
        control_grid.attach(self.vumeter_widget, 0, 1, 1, 1)
        control_grid.attach(self.mute_widget, 1, 0, 1, 1)
        main_grid.attach(info_grid, 0, 0, 1, 1)
        main_grid.attach(control_grid, 0, 1, 1, 1)
        main_grid.attach(connection_grid, 0, 2, 1, 1)

        self.add(main_grid)

        if schema.primary is not None:
            control_grid.attach(self.primary_widget, 2, 0, 1, 1)

    def insert_connection_widget(self, output_type, output_id, connection_schema):
        '''
            Create an output button
        '''
        button = ConnectionWidget(connection_schema, output_type, output_id)
        self.connection_buttons[output_type][output_id] = button
        box = self.connections_box[output_type]
        box.pack_start(button, False, False, 0)
        button.connect('toggled', self.update_connection, output_type, output_id)
        return button

    def remove_connection_widget(self, output_type, output_id):
        button = self.connection_buttons[output_type].pop(output_id)
        del self.schema.connections[output_type][output_id]
        box = self.connections_box[output_type]
        box.remove(button)
        button.destroy()

    def update_volume_schema(self, _):
        volume = self.get_volume()
        self.schema.volume = [volume] * self.schema.channels

    def update_connection(self, button, device_type, device_id):
        state = button.get_active()
        self.schema.connections[device_type][device_id].state = state
        button.schema.state = state

    def update_mute(self, button, device_type, device_id):
        self.schema.mute = self.mute_widget.get_active()

    def get_nick(self) -> str:
        return self.name_widget.nick

    def get_description(self) -> str:
        return self.name_widget.description

    def get_volume(self) -> int:
        return self.volume_widget.get_value()

    def to_schema(self) -> DeviceSchema:
        return self.schema
