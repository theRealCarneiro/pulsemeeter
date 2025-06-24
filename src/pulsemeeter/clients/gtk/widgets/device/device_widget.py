import gettext

from pulsemeeter.schemas.device_schema import ConnectionSchema
# from pulsemeeter.clients.gtk.widgets.common
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget
from pulsemeeter.clients.gtk.widgets.common.mute_widget import MuteWidget
from pulsemeeter.clients.gtk.widgets.common.default_widget import DefaultWidget
from pulsemeeter.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton

# from pulsemeeter.clients.gtk.widgets.device.connection_widget import ConnectionWidget
from pulsemeeter.clients.gtk.widgets.device.connection_box_widget import ConnectionBoxWidget
from pulsemeeter.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup
# from pulsemeeter.clients.gtk.widgets.common.create_device_widget import CreateDevice

from pulsemeeter.clients.gtk.widgets.device.name_widget import NameWidget

from pulsemeeter.clients.gtk.adapters.device_adapter import DeviceAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceWidget(Gtk.Frame, DeviceAdapter):

    __gsignals__ = {
        "mute": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "primary": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "volume": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        "remove_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        "device_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        "update_connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT))
    }

    def __init__(self, model: DeviceModel):
        Gtk.Frame.__init__(self)
        self.get_style_context().add_class("device-frame")

        self.handlers = {}
        self.model = model
        device_type = model.get_type()

        # create containers
        main_grid = Gtk.Grid(margin=5, hexpand=True)
        info_grid = Gtk.Grid(margin_start=5, hexpand=True)
        control_grid = Gtk.Grid(hexpand=True)
        # self.connection_box = {}
        if device_type in ('vi', 'hi'):
            self.connections_widget = ConnectionBoxWidget(device_type, model.connections)

        self.edit_button = IconButton('document-edit-symbolic')
        self.edit_button.set_halign(Gtk.Align.END)

        # self.edit_device_widget = CreateDevice(device_type, device_list)
        self.name_widget = NameWidget(model.nick, model.description)
        self.volume_widget = VolumeWidget(model.volume[0])
        self.mute_widget = MuteWidget(state=model.mute)
        self.vumeter_widget = VumeterWidget()

        # if model.primary is not None:
        self.primary_widget = DefaultWidget(state=model.primary)

        # atatch widgets to containers
        info_grid.attach(self.name_widget, 0, 0, 1, 1)
        info_grid.attach(Gtk.HBox(hexpand=True, halign=Gtk.Align.FILL), 2, 0, 1, 1)
        info_grid.attach(self.edit_button, 2, 0, 1, 1)
        control_grid.attach(self.volume_widget, 0, 0, 1, 1)
        control_grid.attach(self.vumeter_widget, 0, 1, 1, 1)
        control_grid.attach(self.mute_widget, 1, 0, 1, 1)
        main_grid.attach(info_grid, 0, 0, 1, 1)
        main_grid.attach(control_grid, 0, 1, 1, 1)

        if device_type in ('vi', 'hi'):
            main_grid.attach(self.connections_widget, 0, 2, 1, 1)

        # get what popup should be used
        popup_type = HardwareDevicePopup if model.device_class == 'hardware' else VirtualDevicePopup
        self.popover = popup_type(self.model.get_type(), device_model=model)
        self.popover.set_relative_to(self.edit_button)

        self.add(main_grid)

        if model.primary is not None:
            control_grid.attach(self.primary_widget, 2, 0, 1, 1)

        # self.set_can_focus(True)
        self.name_widget.set_can_focus(True)
        accessible_name = self.name_widget.get_full_name()
        self.get_accessible().set_name(accessible_name)

        self.volume_widget.get_accessible().set_name(_("Volume"))
        self.mute_widget.get_accessible().set_name(_("Mute"))
        self.edit_button.get_accessible().set_name(_("Edit"))
        self.primary_widget.get_accessible().set_name(_("Primary"))

        super().__init__(model=model)
        self.show_all()
