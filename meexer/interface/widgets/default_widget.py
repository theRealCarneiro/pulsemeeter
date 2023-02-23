import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


class DefaultWidget(Gtk.ToggleButton):

    def __init__(self, state: bool):
        icon = Gio.ThemedIcon(name='emblem-default-symbolic')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        super().__init__(
            active=state,
            hexpand=False,
            vexpand=False,
            valign=Gtk.Align.CENTER,
            image=image
        )

    def set_state(self, state: bool):
        '''
        Manually change the state of the button
        '''
        self.handler_block_by_func(self.on_toggled)
        self.set_active(state)
        self.handler_unblock_by_func(self.on_toggled)