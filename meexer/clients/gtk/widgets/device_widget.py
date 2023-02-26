import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema

from meexer.clients.gtk.widgets.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.mute_widget import MuteWidget
from meexer.clients.gtk.widgets.default_widget import DefaultWidget
from meexer.clients.gtk.widgets.vumeter_widget import VumeterWidget


class DeviceWidget(Gtk.Frame):

    def __init__(self, device_schema: DeviceSchema):
        super().__init__(margin=10)

        label = device_schema.nick
        if device_schema.nick != device_schema.description:
            label += f': {device_schema.description}'

        # print(device_schema)
        # create widgets
        self.label = Gtk.Label(label=label)
        self.volume = VolumeWidget(device_schema.volume[0])
        self.mute = MuteWidget(state=device_schema.mute)
        # if device_schema.primary is not None:
        self.default = DefaultWidget(state=device_schema.primary)
        self.vumeter = VumeterWidget()
        # TODO: plugins

        # create grids
        main_grid = Gtk.Grid(margin=5, hexpand=True)
        info_grid = Gtk.Grid(margin_start=8, hexpand=True)
        connection_grid = Gtk.Grid(hexpand=True)
        control_grid = Gtk.Grid(hexpand=True)

        # create connection buttons
        self.connection_buttons = {'a': {}, 'b': {}}
        self.connections_box = {'a': Gtk.Box(), 'b': Gtk.Box()}
        for output_type, outputs in device_schema.connections.items():
            for output_id, output in outputs.items():
                self.create_output_button(output_type, output_id, output.nick)

        self.add(main_grid)

        main_grid.attach(info_grid, 0, 0, 1, 1)
        main_grid.attach(control_grid, 0, 1, 1, 1)
        main_grid.attach(connection_grid, 0, 2, 1, 1)

        info_grid.attach(self.label, 0, 0, 1, 1)

        connection_grid.attach(self.connections_box['a'], 0, 0, 1, 1)
        connection_grid.attach(self.connections_box['b'], 1, 0, 1, 1)

        control_grid.attach(self.volume, 0, 0, 1, 1)
        control_grid.attach(self.vumeter, 0, 1, 1, 1)
        control_grid.attach(self.mute, 1, 0, 1, 1)

        if device_schema.primary is not None:
            control_grid.attach(self.default, 2, 0, 1, 1)

    def create_output_button(self, output_type, output_id, nick):
        button = Gtk.ToggleButton(label=nick)
        self.connection_buttons[output_type][output_id] = button
        box = self.connections_box[output_type]
        box.pack_start(button, False, False, 0)

    def remove_output_button(self, output_type, output_id):
        button = self.connection_buttons[output_type].pop(output_id)
        box = self.connections_box[output_type]
        box.remove(button)
        button.destroy()

    # def to_device_schema(self):
        # for device_type, buttons in self.connection_buttons.items():
            # for device_id, button in buttons:
                # self.device_schema.connections[device_type][device_id]


d = DeviceSchema(
    name='test',
    description='testing',
    channels=2,
    channel_list=[],
    device_type='sink',
    device_class='virtual',
    volume=[70, 70],
    connections={'a': {'1': ConnectionSchema(target='test', nick='test')}}
)

# window = Gtk.Window()
# window.add(DeviceWidget(d))
# window.show_all()
# window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
# Gtk.main()
