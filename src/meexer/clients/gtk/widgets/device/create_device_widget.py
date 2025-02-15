from typing import Literal

from meexer.schemas.device_schema import DeviceSchema, CHANNEL_MAPS, INVERSE_CHANNEL_MAPS
from meexer.clients.gtk.widgets.common.input_widget import InputWidget
from meexer.clients.gtk.widgets.common.icon_button_widget import IconButton
from meexer.clients.gtk.widgets.common.combobox_widget import LabeledCombobox
from meexer.clients.gtk.widgets.device.port_selector_widget import PortSelector

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DevicePopup(Gtk.Popover):
    '''
    A widget for creating a new device
    '''

    name_widget: InputWidget
    combobox_widget: LabeledCombobox
    port_selector: PortSelector
    device_list: list[DeviceSchema]
    device_type: Literal['a', 'b', 'hi', 'vi']
    confirm_button: IconButton
    cancel_button: IconButton
    selected_device: DeviceSchema

    def __init__(self):
        super().__init__()

    def device_combo_changed(self, combo):
        active = combo.get_active()
        device = self.device_list[active]
        self.name_widget.input.set_text(device['description'])
        self.port_selector.set_ports(device['channel_list'])
        self.selected_device = device

    @property
    def name(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.name_widget.get_option()

        # if hardware
        return self.selected_device['name']

    @property
    def nick(self):
        return self.name_widget.get_option()

    @property
    def description(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.name_widget.get_option()

        # if hardware
        return self.selected_device['description']

    @property
    def channels(self):
        return len(self.channel_list)

    @property
    def selected_channels(self):

        # if hardware
        if self.device_type in ('a', 'hi'):
            return self.port_selector.get_selected()
        return [True] * self.channels

    @property
    def channel_list(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            channel_map = self.combobox_widget.get_active_text()
            channel_list = CHANNEL_MAPS[channel_map]
            return channel_list

        # if hardware

        selected_channels = self.selected_channels
        channel_list = []

        # only grab channels that are sellected
        for channel, selected_channel in enumerate(selected_channels):
            if selected_channel is True:
                channel_list.append(self.selected_device['channel_list'][channel])

        return channel_list

    @property
    def volume(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return [100] * self.channels

        # if hardware
        selected_channels = self.selected_channels
        volume_list = []
        for channel, selected_channel in enumerate(selected_channels):
            if selected_channel is True:
                volume_list.append(self.selected_device['volume'][channel])

        return volume_list

    def to_schema(self) -> dict:

        device_type = 'sink' if self.device_type in ('a', 'vi') else 'source'
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'

        data = {
            'name': self.name,
            'description': self.description,
            'nick': self.nick,
            'channels': self.channels,
            'channel_list': self.channel_list,
            'selected_channels': self.selected_channels,
            'volume': self.volume,
            'device_type': device_type,
            'device_class': device_class
        }

        return data

    def close_pressed(self, _):
        self.popdown()


class HardwareDevicePopup(DevicePopup):

    def __init__(self, device_type, device_list=None, device_schema: DeviceSchema = None):
        super().__init__()

        self.device_list = device_list
        self.device_type = device_type

        # create widgets
        self.name_widget = InputWidget('Nick: ')
        self.port_selector = PortSelector()
        self.combobox_widget = LabeledCombobox('Device: ')
        self.confirm_button = IconButton('check-filled')
        self.cancel_button = IconButton('cancel')

        if device_schema is not None:
            self.name_widget.set_option(device_schema.nick)
            # self.combobox_widget.empty(device_schema.nick)
            self.port_selector.set_ports(device_schema.selected_channels)

        # load device combobox
        if device_list is not None:
            self.combobox_widget.load_list(device_list, 'description')

        # connect events
        self.combobox_widget.combobox.connect("move-active", self.device_combo_changed)
        self.cancel_button.connect('pressed', self.close_pressed)

        # add widgets to grid
        button_box = Gtk.HBox(halign=Gtk.Align.END)
        button_box.pack_start(self.cancel_button, False, False, 2)
        button_box.pack_start(self.confirm_button, False, False, 2)

        main_box = Gtk.VBox(margin=10, hexpand=True)
        main_box.pack_start(self.name_widget, False, False, 10)
        main_box.pack_start(self.combobox_widget, False, False, 10)
        main_box.pack_start(self.port_selector, False, False, 10)
        main_box.pack_start(button_box, False, False, 5)

        self.set_modal(False)
        self.add(main_box)
        # self.show_all()


class VirtualDevicePopup(DevicePopup):
    def __init__(self, device_type, device_list=None, device_schema: DeviceSchema = None):
        super().__init__()

        self.device_type = device_type

        # create widgets
        self.name_widget = InputWidget('Nick: ')
        self.combobox_widget = LabeledCombobox('Channel Map: ')
        self.confirm_button = IconButton('check-filled')
        self.cancel_button = IconButton('cancel')
        self.combobox_widget.load_list(list(CHANNEL_MAPS))

        if device_schema is not None:
            self.name_widget.set_option(device_schema.nick)
            self.combobox_widget.combobox.set_active(int(INVERSE_CHANNEL_MAPS[device_schema.channels]) - 1)
            # self.port_selector.set_ports(device_schema.selected_channels)

        # connect events
        self.cancel_button.connect('pressed', self.close_pressed)

        # add widgets to grid
        button_box = Gtk.HBox(halign=Gtk.Align.END)
        button_box.pack_start(self.cancel_button, False, False, 2)
        button_box.pack_start(self.confirm_button, False, False, 2)

        main_box = Gtk.VBox(margin=10, hexpand=True)
        main_box.pack_start(self.name_widget, False, False, 10)
        main_box.pack_start(self.combobox_widget, False, False, 10)
        main_box.pack_start(button_box, False, False, 5)

        self.set_modal(False)
        self.add(main_box)
        # self.show_all()
