import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class VolumeWidget(Gtk.Scale):

    __gsignals__ = {
        'volume': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (int,)),
    }

    def __init__(self, value: int = 100, *args, **kwargs):
        self.blocked: bool = False
        self.is_pressed: bool = False
        self.scroll_lock_timeout = None
        self._signal_handler_id = None

        super().__init__(*args, **kwargs)

        self.set_range(0, 153)
        self.set_increments(1, 5)
        self.set_digits(0)
        self.set_value(value)
        self.add_mark(100, Gtk.PositionType.TOP, '')

        Gtk.Accessible.update_property(
            self,
            [
                Gtk.AccessibleProperty.LABEL
            ],
            [
                _('Volume Slider')
            ]
        )
        self.set_tooltip_text(_('Volume Slider'))

        self._setup_gesture_controllers()
        self._signal_handler_id = self.connect('value-changed', self._on_value_changed)

    def _setup_gesture_controllers(self):
        '''Setup gesture controllers for GTK 4 event handling'''
        # Scroll controller
        scroll_controller = Gtk.EventControllerScroll()
        scroll_controller.connect('scroll', self._on_scroll_event)
        self.add_controller(scroll_controller)

        # Click controller for press/release events
        gesture = Gtk.GestureClick()

        # Search for scale internal click controller
        controllers = self.observe_controllers()
        for controller in controllers:
            if isinstance(controller, gi.repository.Gtk.GestureClick):
                gesture = controller

        gesture.set_button(0)
        gesture.connect('pressed', self._on_button_press)
        gesture.connect('released', self._on_button_release)

    def _on_scroll_event(self, controller, dx, dy):
        if self.is_pressed is True:
            return True

        self.blocked = True
        # print('Scroll locked: ', True)

        if self.scroll_lock_timeout is not None:
            GLib.source_remove(self.scroll_lock_timeout)

        self.scroll_lock_timeout = GLib.timeout_add(100, self._clear_scroll_lock)

        # process the other events regularly
        return False

    def _on_button_press(self, *_):
        # print('BUTTON LOCKED: ', True)
        self.blocked = True
        print("block")
        self.is_pressed = True

    def _on_button_release(self, *_):
        # print('BUTTON LOCKED: ', False)
        print("unblock")
        self.blocked = False
        self.is_pressed = False

    def _clear_scroll_lock(self):
        # print('Scroll locked: ', False)
        self.blocked = False
        self.scroll_lock_timeout = None
        return False

    def _on_value_changed(self, widget):
        self.emit('volume', widget.get_value())

    def set_volume(self, value):
        if self.blocked is True:
            return

        self.handler_block(self._signal_handler_id)
        self.set_value(value)
        self.handler_unblock(self._signal_handler_id)

    def get_volume(self):
        return self.get_value()
