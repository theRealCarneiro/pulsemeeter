import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

def dismiss_on_outside_click(popover: Gtk.Popover):
    def on_pressed(gesture, _n_press, x, y):
        if 0 <= x <= popover.get_width() and 0 <= y <= popover.get_height():
            return

        popover.popdown()
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    gesture = Gtk.GestureClick.new()
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    gesture.connect('pressed', on_pressed)
    popover.add_controller(gesture)
