import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class VolumeWidget(Gtk.Scale):

    def __init__(self, value: int = 100):

        print(value)
        self.adjustment = Gtk.Adjustment(
            value=value,
            lower=0,
            upper=153,
            step_increment=1,
            page_increment=10
        )

        super().__init__(
            hexpand=True,
            adjustment=self.adjustment,
            round_digits=0,
            digits=0,
            width_request=100
        )

        self.add_mark(100, Gtk.PositionType.TOP, '')
        self.signal_handler = {}

    def set_state(self, value: int):
        '''
        Changes the state of a connection without calling the signal
        '''
        self.value = value
        self.handler_block_by_func(self.value_change)
        self.set_value(value)
        self.handler_unblock_by_func(self.value_change)
