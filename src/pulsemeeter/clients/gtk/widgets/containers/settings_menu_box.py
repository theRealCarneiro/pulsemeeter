import gettext

# from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.common.dropdown_widget import LabeledDropDown
# from pulsemeeter.clients.gtk import layouts
from pulsemeeter.clients.gtk.layouts import layout_manager

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class SettingsMenuBox(Gtk.Box):

    vumeters: Gtk.CheckButton
    cleanup: bool = False
    tray: bool = False
    layout: str = 'Blocks'

    __gsignals__ = {
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self):
        super().__init__()
        # self.get_accessible().set_name(_('Settings'))
        # self.config_model = config_model
        self.vumeters = Gtk.CheckButton(label=_('Enable VU Meters'))
        self.cleanup = Gtk.CheckButton(label=_('Enable Cleanup'))
        self.tray = Gtk.CheckButton(label=_('Enable Tray'))
        self.layout = LabeledDropDown(_('Layout '))
        # self.vumeters = Gtk.CheckButton(active=config_model.vumeters, label=_('Enable VU Meters'))
        # self.cleanup = Gtk.CheckButton(active=config_model.cleanup, label=_('Enable Cleanup'))
        # self.tray = Gtk.CheckButton(active=config_model.tray, label=_('Enable Tray'))
        self.layout.load_list(layout_manager.get_layout_list())

        # self.tray.get_accessible().set_name(_('Tray'))
        # self.vumeters.get_accessible().set_name(_('VU Meters'))
        # self.cleanup.get_accessible().set_name(_('Cleanup'))
        # self.layout.get_accessible().set_name(_('Layout'))
        self.apply_button = Gtk.Button(label=_('Apply'))
        self.tray.set_tooltip_text(_('Enable or disable %s') % ('closing to the tray'))
        self.vumeters.set_tooltip_text(_('Enable or disable %s') % _('VU Meter (volume peak)'))
        self.cleanup.set_tooltip_text(_('Enable or disable %s') % ('cleaning up devices and connections upon closing'))
        self.layout.set_tooltip_text(_('Select the GUI layout'))

        button_box = Gtk.Box(vexpand=False, halign=Gtk.Align.END, valign=Gtk.Align.END)
        button_box.append(self.apply_button)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mainbox.append(self.vumeters)
        mainbox.append(self.cleanup)
        # mainbox.append(self.tray)
        mainbox.append(self.layout)
        mainbox.append(button_box)

        self.apply_button.connect('clicked', self.apply_settings)

        self.append(mainbox)

    def fill_settings(self, config_model):
        self.tray.set_active(config_model.tray)
        self.vumeters.set_active(config_model.vumeters)
        self.cleanup.set_active(config_model.cleanup)
        self.layout.set_active_name(config_model.layout)

    def to_schema(self):
        return {
            'vumeters': self.vumeters.get_active(),
            'cleanup': self.cleanup.get_active(),
            'tray': self.tray.get_active(),
            'layout': self.layout.get_active_text(),
        }

    def apply_settings(self, _):
        self.emit('settings_change', self.to_schema())
