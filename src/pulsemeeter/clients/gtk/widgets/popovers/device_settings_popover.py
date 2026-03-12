import gettext

from pulsemeeter.schemas import pulse_mappings
# from pulsemeeter.model.device_model import DeviceModel
# from pulsemeeter.schemas.device_schema import CHANNEL_MAPS, INVERSE_CHANNEL_MAPS
from pulsemeeter.clients.gtk.widgets.utils.input_widget import InputWidget
from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.common.dropdown_widget import LabeledDropDown
from pulsemeeter.clients.gtk.widgets.common.port_selector_widget import PortSelector

# from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceSettingsPopover(Gtk.Popover):
    '''

    '''
    def __init__(self, device_type, edit=False):
        super().__init__()
        self.device_type = device_type
        self.edit = edit

        self.nick_widget = InputWidget(_('Nick: '))
        self.name_widget = InputWidget(_('Name: '))
        self.external_widget = Gtk.CheckButton(label=_('External'))
        self.port_selector = PortSelector()
        self.combobox_widget = LabeledDropDown(_('Device: ') if device_type in ('a', 'hi') else _('Channel Map: '))
        self.combobox_widget.disable_dropdown_autohide()
        self.confirm_button = Gtk.Button(label='Apply')
        self.remove_button = IconButton('user-trash-symbolic')
        # self.confirm_button = IconButton('emblem-ok-symbolic')
        # self.cancel_button = IconButton('window-close-symbolic')

        if device_type in ('vi', 'b'):
            self.combobox_widget.load_list(list(pulse_mappings.CHANNEL_MAPS))
        else:
            self.combobox_widget.connect('changed', self.device_combo_changed)

        self._arrange_widgets()

    def _arrange_widgets(self):

        # Create main container
        main_box = Gtk.Box(hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.set_child(main_box)

        # Create name container
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_box.append(self.nick_widget)
        if self.device_type in ('vi', 'b'):
            name_box.append(self.name_widget)

        # Create buttons container
        button_box = Gtk.Box(halign=Gtk.Align.END)
        if self.edit is True:
            button_box.append(self.remove_button)
        button_box.append(self.confirm_button)

        # Insert containers into main container
        main_box.append(name_box)
        main_box.append(self.combobox_widget)
        if self.device_type in ('hi', 'a'):
            main_box.append(self.port_selector)
        else:
            main_box.append(self.external_widget)
        main_box.append(button_box)

    def fill_settings(self, device_model):

        self.nick_widget.set_option(device_model.nick)
        if self.device_type in ('hi', 'a'):
            self.port_selector.set_ports(device_model.selected_channels)
            self.combobox_widget.set_active_name(device_model.description)
        else:
            self.name_widget.set_option(device_model.name)
            self.external_widget.set_active(device_model.external)
            self.combobox_widget.set_active_name(pulse_mappings.get_channel_map_name(device_model.channel_list))

    def device_combo_changed(self, widget, active_text):
        device = self.combobox_widget.get_active_entry()

        self.port_selector.set_ports(device.channel_list)

    @property
    def name(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.name_widget.get_option()

        # if hardware
        return self.combobox_widget.get_active_entry().name

    @property
    def nick(self):
        return self.nick_widget.get_option()

    @property
    def description(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.nick_widget.get_option()

        # if hardware
        return self.combobox_widget.get_active_entry().description

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
            channel_list = pulse_mappings.CHANNEL_MAPS[channel_map]
            return channel_list

        # if hardware

        selected_channels = self.selected_channels
        channel_list = []

        # only grab channels that are sellected
        for channel, selected_channel in enumerate(selected_channels):
            if selected_channel is True:
                selected_device = self.combobox_widget.get_active_entry()
                channel_list.append(selected_device.channel_list[channel])

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
                selected_device = self.combobox_widget.get_active_entry()
                volume_list.append(selected_device.volume[channel])

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
