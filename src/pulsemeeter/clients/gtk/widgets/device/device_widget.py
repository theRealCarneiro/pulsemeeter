import gettext

from pulsemeeter.model import device_model
from pulsemeeter.model.types import DEVICE_TYPE_PRETTY
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton

from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget
from pulsemeeter.clients.gtk.widgets.common.mute_widget import MuteWidget
from pulsemeeter.clients.gtk.widgets.common.default_widget import DefaultWidget
from pulsemeeter.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from pulsemeeter.clients.gtk.widgets.utils.widget_box import WidgetBox
from pulsemeeter.clients.gtk.widgets.device.connection_widget import ConnectionWidget
# from pulsemeeter.clients.gtk.widgets.containers.connection_box_widget import ConnectionBoxWidget
# from pulsemeeter.clients.gtk.widgets.popovers.device_settings_popover import VirtualDevicePopup, HardwareDevicePopup
from pulsemeeter.clients.gtk.widgets.popovers.device_settings_popover import DeviceSettingsPopover

# from pulsemeeter.clients.gtk.adapters.device_settings_adapter import DeviceSettingsAdapter
# from pulsemeeter.clients.gtk.adapters.connection_box_adapter import ConnectionBoxAdapter

# from pulsemeeter.clients.gtk.widgets.device.name_widget import NameWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GObject, Gtk, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceWidget(Gtk.Frame):

    __gsignals__ = {
        'mute': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'primary': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'volume': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'device_remove': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'device_change': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        'connection': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        'update_connection': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT)),
        'settings_pressed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        'connection_settings_pressed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str))
    }

    def __init__(self, model: DeviceModel, layout_style='bars'):
        super().__init__()
        self.get_style_context().add_class('device-frame')
        self.handlers = {}
        self.device_model = model
        self._create_widgets(model)
        self._connect_callbacks()

    def _create_widgets(self, model):
        # self.name_widget = NameWidget(model.nick, model.description)
        self.nick_label = Gtk.Label()
        self.nick_label.set_markup(f'<b>{self.device_model.nick}</b>')
        self.description_label = Gtk.Label(label=self.device_model.description)
        self.description_label.set_visible(self.device_model.nick != self.device_model.description)
        self.name_label = Gtk.Label(label=self.device_model.name)
        self.volume_widget = VolumeWidget(value=model.volume[0], draw_value=True)
        self.mute_widget = MuteWidget(active=model.mute)
        self.vumeter_widget = VumeterWidget()
        # self.edit_button = IconButton('document-edit-symbolic')
        self.edit_button = Gtk.MenuButton()
        self.edit_button.set_label('Settings Menu')
        self.edit_button.set_icon_name('open-menu-symbolic')
        self.edit_button.set_tooltip_text('Click to open settings menu')
        # popup_type = HardwareDevicePopup if model.device_class == 'hardware' else VirtualDevicePopup
        self.popover = DeviceSettingsPopover(model.get_type(), edit=True)
        self.edit_button.set_popover(self.popover)
        # self.popover.set_relative_to(self.edit_button)

        # if model.primary is not None:
        self.primary_widget = DefaultWidget(active=model.primary)
        self.connections_widgets = {}

        if model.get_type() in ('vi', 'hi'):
            self.connections_widgets = {'a': WidgetBox(), 'b': WidgetBox()}
            self._create_connection_widgets()

        Gtk.Accessible.update_property(
            self,
            [
                Gtk.AccessibleProperty.LABEL,
            ],
            [
                self.get_accessible_name(),
            ]
        )

        self.edit_button.set_tooltip_text(_('Open device settings'))
        Gtk.Accessible.update_property(
            self.edit_button,
            [
                Gtk.AccessibleProperty.LABEL,
                Gtk.AccessibleProperty.DESCRIPTION,
                Gtk.AccessibleProperty.HAS_POPUP,
            ],
            [
                _('Device settings'),
                _('Open device settings'),
                True
            ]
        )

        self.nick_label.set_can_focus(True)

    def get_accessible_name(self):
        accessible_name = self.device_model.nick
        if self.device_model.nick != self.device_model.description:
            accessible_name += f' {self.device_model.description}'

        return accessible_name

    def fill_settings(self):
        self.volume_widget.set_volume(self.device_model.volume[0])
        self.mute_widget.set_mute(self.device_model.mute)
        self.nick_label.set_label(self.device_model.nick)
        self.description_label.set_label(self.device_model.description)
        self.description_label.set_visible(self.device_model.nick != self.device_model.description)

    def reload_connection_widgets(self):
        self.connections_widgets['a'].clear()
        self.connections_widgets['b'].clear()
        self._create_connection_widgets()

    def _create_connection_widgets(self):
        for output_type in ('a', 'b'):
            for output_id, connection_schema in self.device_model.connections[output_type].items():
                button = ConnectionWidget(connection_schema.nick, connection_schema)
                self.connections_widgets[output_type].add_widget(output_id, button)
                button.connect('connection', self._on_connection_change, output_type, output_id)
                button.connect('settings_pressed', self._on_connection_edit_pressed, output_type, output_id)
                button.popover.confirm_button.connect('clicked', self._on_connection_settings_save, output_type, output_id)

    def _connect_callbacks(self):
        self.volume_widget.connect('volume', self._on_volume_change)
        self.mute_widget.connect('mute', self._on_mute_change)
        self.primary_widget.connect('primary', self._on_primary_change)
        self.popover.confirm_button.connect('clicked', self._on_settings_save)
        self.popover.remove_button.connect('clicked', self._on_device_remove)

        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self._on_edit_pressed)
        self.edit_button.add_controller(gesture)

    def _on_device_remove(self, _):
        self.emit('device_remove')

    def _on_volume_change(self, _, value):
        self.emit('volume', value)

    def _on_connection_change(self, _, state, output_type, output_id):
        self.emit('connection', output_type, output_id, state)

    def _on_mute_change(self, _, state):
        self.emit('mute', state)

    def _on_primary_change(self, _):
        self.emit('primary')

    def _on_connection_settings_save(self, _, output_type, output_id):
        popover = self.connections_widgets[output_type].widgets[output_id].popover
        schema = popover.get_connection_model()
        self.emit('update_connection', output_type, output_id, schema)

    def _on_settings_save(self, _):
        schema = self.popover.to_schema()
        if len(schema['nick'].strip()) != 0:
            self.emit('device_change', schema)

    def _on_edit_pressed(self, *_):
        self.emit('settings_pressed', self.popover)

    def _on_connection_edit_pressed(self, _, output_type, output_id):
        self.emit('connection_settings_pressed', output_type, output_id)

    def pa_device_change(self):
        volume = self.device_model.volume[0]
        mute = self.device_model.mute

        if self.volume_widget.get_volume() != volume:
            self.volume_widget.set_volume(volume)

        if self.mute_widget.get_mute() != mute:
            self.mute_widget.set_mute(mute)

    # def edit_device_popover(self, _):
    #     self.popover.show_all()
    #     self.popover.fill_settings(self.device_model)
    #     self.popover.popup()
    #     device_type = self.device_model.get_type()
    #     self.emit('settings_pressed', self.device_model, self.popover)
    #     self.popover.nick_widget.input.grab_focus()
