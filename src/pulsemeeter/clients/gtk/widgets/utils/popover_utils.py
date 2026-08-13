# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def dismiss_on_outside_click(popover: Gtk.Popover):
    '''
    Manually make a popover close when clicked outside of it.

    Nested popovers break the parent popovers dismissal when the child popover
    opens. Instead we manually check for a click outside of the parent popovers
    bounds no matter if the nested popover is open.

    See GNOME/gtk#4529, fixed upstream by gtk!9895 ("Rework GDK grabs") 
    for GTK 4.24. Until GTK 4.24 is mainstream, manually closing the popover is
    the workaround. Can be removed if we switch off nested popovers.
    '''

    def on_pressed(gesture, _n_press, x, y):
        if 0 <= x <= popover.get_width() and 0 <= y <= popover.get_height():
            return

        popover.popdown()
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    gesture = Gtk.GestureClick.new()
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    gesture.connect('pressed', on_pressed)
    popover.add_controller(gesture)
