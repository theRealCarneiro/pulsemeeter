import gettext

from typing import Literal

from pulsemeeter.schemas import pulse_mappings
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.schemas.device_schema import CHANNEL_MAPS, INVERSE_CHANNEL_MAPS
from pulsemeeter.clients.gtk.widgets.common.input_widget import InputWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.common.combobox_widget import LabeledCombobox
from pulsemeeter.clients.gtk.widgets.device.port_selector_widget import PortSelector

from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class HardwareDevicePopup(Gtk.Popover, DeviceSettingsAdapter):

    def __init__(self, device_type, device_list=None, device_model: DeviceModel = None):

        Gtk.Popover.__init__(self)
        DeviceSettingsAdapter.__init__(self)
        dt = 'Output' if device_type == 'a' else 'Input'
        operation = "Create" if device_model is None else "Edit"
        self.get_accessible().set_name(_(f'{operation} hardware {dt} device popover'))

        self.device_list = device_list
        self.device_type = device_type

        # create widgets
        self.nick_widget = InputWidget(_('Nick: '))
        self.port_selector = PortSelector()
        self.combobox_widget = LabeledCombobox(_('Device: '))
        # self.confirm_button = IconButton('emblem-ok-symbolic')
        self.confirm_button = Gtk.Button('Apply')
        self.cancel_button = IconButton('window-close-symbolic')
        self.remove_button = IconButton('user-trash-symbolic')

        # if device_model is not None:
        #     self.nick_widget.set_option(device_model.nick)
        #     # self.combobox_widget.empty(device_model.nick)
        #     self.port_selector.set_ports(device_model.selected_channels)

        # load device combobox
        if device_list is not None:
            self.combobox_widget.load_list(device_list, 'description')

        # connect events
        self.combobox_widget.combobox.connect('changed', self.device_combo_changed)
        self.cancel_button.connect('clicked', self.close_pressed)

        # add widgets to grid
        button_box = Gtk.HBox(halign=Gtk.Align.END)
        if device_model is not None:
            button_box.pack_start(self.remove_button, False, False, 2)
        button_box.pack_start(self.cancel_button, False, False, 2)
        button_box.pack_start(self.confirm_button, False, False, 2)

        main_box = Gtk.VBox(margin=10, hexpand=True)
        main_box.pack_start(self.nick_widget, False, False, 10)
        main_box.pack_start(self.combobox_widget, False, False, 10)
        main_box.pack_start(self.port_selector, False, False, 10)
        main_box.pack_start(button_box, False, False, 5)

        self.cancel_button.get_accessible().set_name(_("Cancel"))
        self.remove_button.get_accessible().set_name(_("Delete device"))
        self.confirm_button.get_accessible().set_name(_("Create device"))

        self.set_modal(False)
        self.add(main_box)
        # self.show_all()
        # self.nick_widget.input.grab_focus()

    def fill_settings(self, device_model):
        self.nick_widget.set_option(device_model.nick)
        self.port_selector.set_ports(device_model.selected_channels)



class VirtualDevicePopup(Gtk.Popover, DeviceSettingsAdapter):
    def __init__(self, device_type, device_list=None, device_model: DeviceModel = None):
        super().__init__()

        self.device_type = device_type
        dt = 'Output' if device_type == 'a' else 'Input'
        operation = "Create" if device_model is None else "Edit"
        self.get_accessible().set_name(_(f'{operation} virtual {dt} device popover'))

        # create widgets
        self.nick_widget = InputWidget(_('Nick: '))
        self.name_widget = InputWidget(_('Name: '))
        self.external_widget = Gtk.CheckButton(_('External'))
        self.combobox_widget = LabeledCombobox(_('Channel Map: '))
        # self.confirm_button = IconButton('emblem-ok-symbolic')
        self.confirm_button = Gtk.Button('Apply')
        self.cancel_button = IconButton('window-close-symbolic')
        self.remove_button = IconButton('user-trash-symbolic')
        self.combobox_widget.load_list(list(pulse_mappings.CHANNEL_MAPS))

        # if device_model is not None:
        #     self.nick_widget.set_option(device_model.nick)
        #     self.name_widget.set_option(device_model.name)
        #     self.external_widget.set_active(device_model.external)
        #     self.combobox_widget.combobox.set_active(int(INVERSE_CHANNEL_MAPS[device_model.channels]) - 1)
            # self.port_selector.set_ports(device_model.selected_channels)

        name_box = Gtk.VBox()
        name_box.pack_start(self.nick_widget, False, False, 10)
        name_box.pack_start(self.name_widget, False, False, 10)

        # connect events
        self.cancel_button.connect('clicked', self.close_pressed)

        # add widgets to grid
        button_box = Gtk.HBox(halign=Gtk.Align.END)
        if device_model is not None:
            button_box.pack_start(self.remove_button, False, False, 2)
        button_box.pack_start(self.cancel_button, False, False, 2)
        button_box.pack_start(self.confirm_button, False, False, 2)

        main_box = Gtk.VBox(margin=10, hexpand=True)
        main_box.pack_start(name_box, False, False, 10)
        main_box.pack_start(self.external_widget, False, False, 10)
        main_box.pack_start(self.combobox_widget, False, False, 10)
        main_box.pack_start(button_box, False, False, 5)

        self.cancel_button.get_accessible().set_name(_("Cancel"))
        self.remove_button.get_accessible().set_name(_("Delete device"))
        self.confirm_button.get_accessible().set_name(_("Create device"))

        self.set_modal(False)
        self.add(main_box)
        # self.show_all()

    def fill_settings(self, device_model):
        self.nick_widget.set_option(device_model.nick)
        self.name_widget.set_option(device_model.name)
        self.external_widget.set_active(device_model.external)
        # self.combobox_widget.combobox.set_active(int(INVERSE_CHANNEL_MAPS[device_model.channels]) - 1)
        self.combobox_widget.set_active_name(pulse_mappings.get_channel_map_name(device_model.channel_list))
