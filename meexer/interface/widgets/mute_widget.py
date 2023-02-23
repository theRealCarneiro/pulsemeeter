import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


class MuteWidget(Gtk.ToggleButton):

    def __init__(self, state: bool):
        icon = Gio.ThemedIcon(name='audio-volume-muted')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        super().__init__(
            active=state,
            hexpand=False,
            vexpand=False,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.END,
            image=image
        )

        self.signal_handler = {}

    def set_state(self, state: bool, function_to_block):
        '''
        Manually change the state of the button
        '''
        self.handler_block_by_func(self.on_toggled)
        self.set_active(state)
        self.handler_unblock_by_func(self.on_toggled)
