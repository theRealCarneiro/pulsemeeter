import gettext

from pulsemeeter.clients.gtk.widgets.common.dropdown_widget import LabeledDropDown
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
    layout: str = 'Blocks'

    __gsignals__ = {
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "help_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
    }

    def __init__(self):
        super().__init__()
        self.vumeters = Gtk.CheckButton(label=_('Enable VU Meters'))
        self.cleanup = Gtk.CheckButton(label=_('Enable Cleanup'))
        self.layout = LabeledDropDown(_('Layout '))
        self.layout.load_list(layout_manager.get_layout_list())

        self.apply_button = Gtk.Button(label=_('Apply'))
        self.help_button = Gtk.Button(icon_name='help-about-symbolic')
        self.help_button.set_tooltip_text(_('Open the welcome guide'))
        Gtk.Accessible.update_property(
            self.help_button,
            [Gtk.AccessibleProperty.LABEL],
            [_('Open the welcome guide')]
        )
        self.vumeters.set_tooltip_text(_('Enable or disable %s') % _('VU Meter (volume peak)'))
        self.cleanup.set_tooltip_text(_('Enable or disable %s') % ('cleaning up devices and connections upon closing'))
        self.layout.set_tooltip_text(_('Select the GUI layout'))

        button_box = Gtk.Box(vexpand=False, halign=Gtk.Align.END, valign=Gtk.Align.END, spacing=6)
        button_box.append(self.help_button)
        button_box.append(self.apply_button)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mainbox.append(self.vumeters)
        mainbox.append(self.cleanup)
        mainbox.append(self.layout)
        mainbox.append(button_box)

        self.apply_button.connect('clicked', self.apply_settings)
        self.help_button.connect('clicked', lambda _: self.emit('help_pressed'))

        self.append(mainbox)

    def fill_settings(self, config_model):
        self.vumeters.set_active(config_model.vumeters)
        self.cleanup.set_active(config_model.cleanup)
        self.layout.set_active_name(config_model.layout)

    def to_schema(self):
        return {
            'vumeters': self.vumeters.get_active(),
            'cleanup': self.cleanup.get_active(),
            'layout': self.layout.get_active_text(),
        }

    def apply_settings(self, _):
        self.emit('settings_change', self.to_schema())
