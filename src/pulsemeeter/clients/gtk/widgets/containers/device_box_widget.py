import gettext

# from pulsemeeter.model.device_model import DeviceModel
# from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
# from pulsemeeter.clients.gtk.widgets.device.device_settings_popover import VirtualDevicePopup, HardwareDevicePopup

# from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton

# from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter
from pulsemeeter.clients.gtk.widgets.utils.widget_box import WidgetBox

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceBoxWidget(WidgetBox):

    device_type: str
    devices: dict[str, DeviceWidget] = {}
    device_box: Gtk.Box
    add_device_button: IconButton
    popover: DeviceSettingsAdapter

    device_label = {
        'hi': _('Hardware Inputs'),
        'vi': _('Virtual Inputs'),
        'a': _('Hardware Outputs'),
        'b': _('Virtual Outputs'),
    }

    __gsignals__ = {
        "create_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        # "remove_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, device_type):
        super().__init__()

        # set attributes
        self.device_type = device_type
        self.devices: dict[str, DeviceWidget] = {}

        # Create label
        device_type_string = self.device_label[device_type]
        # title = Gtk.Label(device_type_string, margin=10)

        add_button = IconButton('list-add-symbolic')
        add_button.set_tooltip_text(_("Create new %s device") % device_type_string)
        add_button.get_accessible().set_name(_("Create a %s device") % device_type_string)

        title_box = Gtk.HBox()
        title_box.add(title)
        title_box.add(add_button)

        self.get_accessible().set_name(device_type_string)
        self.set_label_widget(title_box)
        self.set_label_align(0.5, 0)

        self.device_box = Gtk.VBox()
        self.add(self.device_box)

        self.title = title
        self.add_device_button = add_button

        # get what popup should be used
        dc = 'hardware' if device_type in ('a', 'hi') else 'virtual'
        popup_type = HardwareDevicePopup if dc == 'hardware' else VirtualDevicePopup
        self.popover = popup_type(device_type)
        self.popover.set_relative_to(self.add_device_button)

        self.popover.confirm_button.connect('clicked', self.create_pressed)
        self.add_device_button.connect('clicked', self.open_popover)

        # self.load_devices(devices_schema)

    def open_popover(self, _):
        '''
            Opens create device popover when clicking on the new device button
        '''

        # create popup
        self.emit('add_device_pressed', self.device_type)
        self.popover.show_all()
        self.popover.popup()
        self.popover.nick_widget.input.grab_focus()

    def create_pressed(self, _):
        schema = self.popover.to_schema()
        self.emit('create_pressed', schema)
        self.popover.popdown()
