import logging

from meexer.model.app_model import AppModel
from meexer.clients.gtk.widgets.common.volume_widget import VolumeWidget
from meexer.clients.gtk.widgets.common.vumeter_widget import VumeterWidget
from meexer.clients.gtk.widgets.common.mute_widget import MuteWidget
from meexer.clients.gtk.widgets.common.icon_widget import IconWidget
from meexer.clients.gtk.widgets.app.app_combobox import AppCombobox

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


LOG = logging.getLogger("generic")


class AppAdapter(GObject.GObject):
    app_model: AppModel
    label: Gtk.Label
    icon: IconWidget
    volume: VolumeWidget
    combobox: AppCombobox
    mute: MuteWidget
    vumeter: VumeterWidget
    handlers: dict[str, int]

    __gsignals__ = {
        "app_mute": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        "app_volume": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        "app_device_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
    }

    def __init__(self):
        super().__init__()
        self.handlers['app_volume'] = self.volume.connect('value-changed', self.update_model_volume)
        self.handlers['app_mute'] = self.mute.connect('toggled', self.update_model_mute)
        self.handlers['app_device_change'] = self.combobox.connect('changed', self.update_model_device)

    def update_model_volume(self, volume: VolumeWidget):
        self.emit('app_volume', volume.get_value())

    def update_model_mute(self, mute: MuteWidget):
        self.emit('app_mute', mute.get_active())

    def update_model_device(self, app_combobox):
        self.emit('app_device_change', app_combobox.get_active_text())

    def set_volume(self, volume):
        self.volume.handler_block(self.handlers['app_volume'])
        self.volume.set_value(volume)
        self.volume.handler_unblock(self.handlers['app_volume'])

    def set_mute(self, mute: bool):
        self.mute.handler_block(self.handlers['app_mute'])
        self.mute.set_active(mute)
        self.mute.handler_unblock(self.handlers['app_mute'])

    def change_device(self):
        self.combobox.handler_block(self.handlers['app_device_change'])
        # self.combobox.set_value(volume)
        self.combobox.handler_unblock(self.handlers['app_device_change'])
