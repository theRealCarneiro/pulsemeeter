from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget
from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class DeviceBoxAdapter(GObject.GObject):

    device_type: str
    device_box = Gtk.Box()
    devices: dict[str, DeviceWidget] = {}
    add_device_button: IconButton
    popover: DeviceSettingsAdapter

    device_label = {
        'hi': 'Hardware Inputs',
        'vi': 'Virtual Inputs',
        'a': 'Hardware Outputs',
        'b': 'Virtual Outputs',
    }

    __gsignals__ = {
        "create_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        "remove_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.popover.confirm_button.connect('clicked', self.create_pressed)
        self.add_device_button.connect('clicked', self.new_device_popup)

    def focus_box(self):
        self.add_device_button.grab_focus()
        # if len(self.devices) == 0: 
        #     return
        # first_item = next(iter(self.devices.values()))
        # first_item.edit_button.grab_focus()

    def load_devices(self, devices_schema: dict[str, DeviceModel]):
        for device_id, device_schema in devices_schema.items():
            self.insert_device(device_schema, device_id)

    def insert_device(self, device_schema: DeviceModel, device_id: str) -> DeviceWidget:
        device = DeviceWidget(device_schema)
        device.connect('remove_pressed', self.remove_pressed, device_id)
        self.device_box.pack_start(device, False, False, 0)
        self.devices[device_id] = device

        # key = Gdk.KEY_1 + len(self.devices)
        # self.accel_group.connect(
        #     key,
        #     0,
        #     Gtk.AccelFlags.VISIBLE,
        #     device.grab_focus()
        # )
        # print('aq')

        return device

    def remove_device(self, device_id: str) -> DeviceWidget:
        device_widget = self.devices.pop(device_id)
        self.remove(device_widget)
        device_widget.destroy()
        return device_widget

    def new_device_popup(self, _):
        '''
            Opens create device popover when clicking on the new device button
        '''

        # create popup
        self.emit('add_device_pressed', self.device_type)
        self.popover.show_all()
        self.popover.popup()
        self.popover.name_widget.input.grab_focus()

    def remove_pressed(self, _, device_type, device_id):
        self.emit('remove_pressed', device_type, device_id)

    def create_pressed(self, _):
        schema = self.popover.to_schema()
        self.emit('create_pressed', schema)
