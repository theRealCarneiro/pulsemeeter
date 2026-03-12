import gettext

from pulsemeeter.model.types import DEVICE_TYPE_PRETTY
from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.utils.widget_box import WidgetBox
from pulsemeeter.clients.gtk.widgets.popovers.device_settings_popover import DeviceSettingsPopover
from pulsemeeter.clients.gtk.widgets.containers.settings_menu_box import SettingsMenuBox
# from pulsemeeter.clients.gtk.widgets.utils.framed_widget import FramedWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class Content(Gtk.Box):

    __gsignals__ = {
        "device_new": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "add_device_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT, str, str)),
        "settings_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_button = Gtk.MenuButton(icon_name='emblem-system-symbolic')
        self.settings_box = SettingsMenuBox()
        # settings_popover = Gtk.Popover()
        # settings_popover.set_child(self.settings_box)
        # self.settings_button.set_popover(settings_popover)

        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self._on_settings_pressed)
        self.settings_button.add_controller(gesture)
        self.settings_box.connect('settings_change', self._on_settings_changed)

        self.create_device_button = {}
        self.device_box = {}
        for device_type in ('a', 'b', 'vi', 'hi'):
            self.device_box[device_type] = WidgetBox()
            self.create_device_button[device_type] = self._new_device_button()
            popover = DeviceSettingsPopover(device_type)
            popover.confirm_button.connect('clicked', self._on_device_create, popover)
            self.create_device_button[device_type].set_popover(popover)
            gesture = Gtk.GestureClick.new()
            gesture.connect("pressed", self._on_add_device_pressed, device_type)
            self.create_device_button[device_type].add_controller(gesture)
            accessible_description = _('Create new %s') % DEVICE_TYPE_PRETTY[device_type][:-1]
            self.create_device_button[device_type].set_tooltip_text(accessible_description)
            Gtk.Accessible.update_property(
                self.create_device_button[device_type],
                [
                    Gtk.AccessibleProperty.LABEL,
                    Gtk.AccessibleProperty.DESCRIPTION,
                    Gtk.AccessibleProperty.HAS_POPUP,
                ],
                [
                    _('Create device'),
                    accessible_description,
                    True
                ]
            )
        self.settings_button.set_tooltip_text(_('Open settings menu'))
        Gtk.Accessible.update_property(
            self.settings_button,
            [
                Gtk.AccessibleProperty.LABEL,
                Gtk.AccessibleProperty.DESCRIPTION,
                Gtk.AccessibleProperty.HAS_POPUP,
            ],
            [
                _('Settings menu'),
                _('Open settings menu'),
                True
            ]
        )

        self.app_box = {'sink_input': WidgetBox(), 'source_output': WidgetBox()}

    def _on_device_create(self, _, popover):
        self.emit('device_new', popover.to_schema())

    def _on_settings_pressed(self, *_):
        self.emit('settings_pressed')

    def _on_settings_changed(self, _, schema):
        self.emit('settings_change', schema)

    def _on_add_device_pressed(self, _, __, ___, ____, device_type):
        popover = self.create_device_button[device_type].get_popover()
        self.emit('add_device_pressed', popover, device_type, None)

    def _new_device_button(self):
        return Gtk.MenuButton(icon_name='list-add-symbolic')
