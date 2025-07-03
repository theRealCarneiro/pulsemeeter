from typing import Literal

from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.schemas.device_schema import CHANNEL_MAPS
from pulsemeeter.clients.gtk.widgets.common.input_widget import InputWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.common.combobox_widget import LabeledCombobox
from pulsemeeter.clients.gtk.widgets.device.port_selector_widget import PortSelector

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceSettingsAdapter(GObject.GObject):
    '''
    A widget for creating a new device
    '''

    nick_widget: InputWidget
    name_widget: InputWidget
    combobox_widget: LabeledCombobox
    port_selector: PortSelector
    device_list: list[DeviceModel]
    device_type: Literal['a', 'b', 'hi', 'vi']
    confirm_button: IconButton
    cancel_button: IconButton
    selected_device: DeviceModel

    def __init__(self):
        super().__init__()
        self.connect("key-press-event", self._on_key_press)
        # if self.combobox_widget
        # self.combobox_widget.combobox.connect('move-active', self.device_combo_changed)

    def _on_key_press(self, widget, event):
        # 65307 is the keyval for Escape
        if event.keyval == Gdk.KEY_Escape:
            self.popdown()
            return True
        return False

    def device_combo_changed(self, combo):
        active = combo.get_active()
        device = self.device_list[active]

        found = False
        cur_nick = self.nick_widget.input.get_text()
        for d in self.device_list:
            if cur_nick == d.description or cur_nick == '':
                found = True
                break

        if found is False:
            self.nick_widget.input.set_text(device.description)

        self.port_selector.set_ports(device.channel_list)
        self.selected_device = device

    @property
    def name(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.name_widget.get_option()

        # if hardware
        return self.selected_device.name

    @property
    def nick(self):
        return self.nick_widget.get_option()

    @property
    def description(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.nick_widget.get_option()

        # if hardware
        return self.selected_device.description

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
                channel_list.append(self.selected_device.channel_list[channel])

        return channel_list

    @property
    def external(self) -> bool:
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'
        if device_class == 'hardware':
            return False

        return self.external_widget.get_active()

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
                volume_list.append(self.selected_device.volume[channel])

        return volume_list

    def to_schema(self) -> dict:

        device_type = 'sink' if self.device_type in ('a', 'vi') else 'source'
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'

        data = {
            'name': self.name,
            'description': self.description,
            'nick': self.nick,
            'external': self.external,
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
