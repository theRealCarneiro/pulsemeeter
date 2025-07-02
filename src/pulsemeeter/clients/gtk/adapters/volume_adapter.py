# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class VolumeAdapter(GObject.GObject):
    adjustment: Gtk.Adjustment
    blocked: bool = False
    is_pressed: bool = False
    scroll_lock_timeout = None

    def __init__(self):
        self.connect("scroll-event", self.on_scroll_event)
        self.connect('button-press-event', self.set_blocked, True)
        self.connect('button-release-event', self.set_blocked, False)

    def on_scroll_event(self, widget, _):
        if self.is_pressed is True:
            return True

        self.blocked = True
        # print('Scroll locked: ', True)

        if self.scroll_lock_timeout is not None:
            GLib.source_remove(self.scroll_lock_timeout)

        self.scroll_lock_timeout = GLib.timeout_add(100, self.clear_scroll_lock)

        # process the other events regularly
        return False

    def clear_scroll_lock(self):
        # print('Scroll locked: ', False)
        self.blocked = False
        self.scroll_lock_timeout = None
        return False

    def set_blocked(self, widget, _, state: bool):
        # print('BUTTON LOCKED: ', state)
        self.blocked = state
        self.is_pressed = state
