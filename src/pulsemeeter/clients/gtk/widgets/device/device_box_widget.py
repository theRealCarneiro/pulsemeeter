from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup
from pulsemeeter.clients.gtk.adapters.device_box_adapter import DeviceBoxAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceBoxWidget(Gtk.Frame, DeviceBoxAdapter):

    device_label = {
        'hi': 'Hardware Inputs',
        'vi': 'Virtual Inputs',
        'a': 'Hardware Outputs',
        'b': 'Virtual Outputs',
    }

    __gsignals__ = {
        "create_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "remove_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, devices_schema: DeviceModel, device_type: str, device_manager):
        Gtk.Frame.__init__(self, margin=5)

        self.device_type = device_type
        self.devices: dict[str, DeviceWidget] = {}
        device_type_string = self.device_label[device_type]

        title = Gtk.Label(device_type_string, margin=10)

        add_button = IconButton('add')

        add_button.set_tooltip_text(f"Create new {device_type_string} device")
        add_button.get_accessible().set_name(f"Create {device_type_string} device")

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
        # self.add_device_button.connect('pressed', self.create_new_device_popover)

        # get what popup should be used
        dc = 'hardware' if device_type in ('a', 'hi') else 'virtual'
        popup_type = HardwareDevicePopup if dc == 'hardware' else VirtualDevicePopup
        self.popover = popup_type(device_type)
        self.popover.set_relative_to(self.add_device_button)
        # self.popover.popdown()

        DeviceBoxAdapter.__init__(self, device_manager=device_manager)

        self.load_devices(devices_schema)
