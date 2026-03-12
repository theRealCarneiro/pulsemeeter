import gettext
import logging

from pulsemeeter.model.app_model import AppModel
# from pulsemeeter.schemas.typing import AppType
from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget
from pulsemeeter.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from pulsemeeter.clients.gtk.widgets.common.mute_widget import MuteWidget
from pulsemeeter.clients.gtk.widgets.utils.icon_widget import IconWidget
from pulsemeeter.clients.gtk.widgets.app.app_dropdown import AppDropDown
# from pulsemeeter.clients.gtk.adapters.app_adapter import AppAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


LOG = logging.getLogger("generic")


class AppWidget(Gtk.Frame):

    __gsignals__ = {
        "app_mute": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "app_volume": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        "app_device": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self, app_model: AppModel):
        self.app_model = app_model
        super().__init__()

        # self.from_model(app_model)
        self.app_type = app_model.app_type
        self.label = Gtk.Label()
        self.label.set_markup(f'<b>{self.app_model.label}</b>')
        self.icon = IconWidget(app_model.icon)
        self.volume_widget = VolumeWidget(value=app_model.volume, draw_value=True)
        self.combobox = AppDropDown(app_model.app_type)
        self.mute_widget = MuteWidget(active=app_model.mute)
        self.vumeter_widget = VumeterWidget()
        self.handlers = {}

        self.combobox.set_active_device(app_model.device)

        Gtk.Accessible.update_property(
            self,
            [
                Gtk.AccessibleProperty.LABEL,
            ],
            [
                app_model.label,
            ]
        )

        self.volume_widget.connect('volume', self._on_volume_change)
        self.mute_widget.connect('mute', self._on_mute_change)
        self._combobox_handler_id = self.combobox.connect('changed', self._on_device_change)

    def _on_volume_change(self, _, value):
        self.emit('app_volume', value)

    def _on_mute_change(self, _, state):
        self.emit('app_mute', state)

    def _on_device_change(self, app_combobox):
        self.emit('app_device', app_combobox.get_active_text())

    def pa_app_change(self, app):
        self.volume_widget.set_volume(app.volume)
        self.mute_widget.set_mute(bool(app.mute))
        self.change_device(app.device)

    def change_device(self, device_name: str):
        if self.combobox.get_active_text() == device_name:
            return

        self.combobox.handler_block(self._combobox_handler_id)
        self.combobox.set_active_device(device_name)
        self.combobox.handler_unblock(self._combobox_handler_id)
