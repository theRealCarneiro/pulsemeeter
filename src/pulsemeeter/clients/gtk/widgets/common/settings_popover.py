import gettext

from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.common.combobox_widget import LabeledCombobox
from pulsemeeter.clients.gtk import layouts

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class SettingsMenuPopover(Gtk.Popover):

    vumeters: Gtk.CheckButton
    cleanup: bool = False
    tray: bool = False
    layout: str = 'blocks'

    __gsignals__ = {
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, config_model):
        Gtk.Popover.__init__(self)
        self.get_accessible().set_name(_('Settings'))
        self.config_model = config_model
        self.vumeters = Gtk.CheckButton(active=config_model.vumeters, label=_('Enable VU Meters'))
        self.cleanup = Gtk.CheckButton(active=config_model.cleanup, label=_('Enable Cleanup'))
        self.tray = Gtk.CheckButton(active=config_model.tray, label=_('Enable Tray'))
        self.layout = LabeledCombobox(_('Layout'))
        self.layout.load_list(layouts.LAYOUTS, selected=config_model.layout)

        self.apply_button = Gtk.Button(label=_('Apply'))
        # cancel_button = Gtk.Button(label=_('Cancel'))
        self.cancel_button = IconButton('window-close-symbolic')

        self.cancel_button.connect('clicked', self.close_pressed)

        self.tray.get_accessible().set_name(_('Tray'))
        self.tray.set_tooltip_text(_('Enable or disable %s') % ('closing to the tray'))
        self.vumeters.get_accessible().set_name(_('VU Meters'))
        self.vumeters.set_tooltip_text(_('Enable or disable %s') % _('VU Meter (volume peak)'))
        self.cleanup.get_accessible().set_name(_('Cleanup'))
        self.cleanup.set_tooltip_text(_('Enable or disable %s') % ('cleaning up devices and connections upon closing'))
        self.layout.get_accessible().set_name(_('Layout'))
        self.layout.set_tooltip_text(_('Select the GUI layout'))

        button_box = Gtk.HBox(halign=Gtk.Align.END)
        button_box.pack_start(self.cancel_button, False, False, 5)
        button_box.pack_start(self.apply_button, False, False, 5)

        mainbox = Gtk.VBox()
        mainbox.pack_start(self.vumeters, False, False, 5)
        mainbox.pack_start(self.cleanup, False, False, 5)
        mainbox.pack_start(self.tray, False, False, 5)
        mainbox.pack_start(self.layout, False, False, 5)
        mainbox.pack_start(button_box, False, False, 5)

        self.apply_button.connect('clicked', self.apply_settings)

        self.set_modal(False)
        self.add(mainbox)

    def to_schema(self):
        return {
            'vumeters': self.vumeters.get_active(),
            'cleanup': self.cleanup.get_active(),
            'tray': self.tray.get_active(),
            'layout': self.layout.get_active_text(),
        }

    def open_settings(self, _):
        self.popup()
        self.show_all()

    def apply_settings(self, _):
        self.emit('settings_change', self.to_schema())

    def close_pressed(self, _):
        self.popdown()
        # self.destroy()
