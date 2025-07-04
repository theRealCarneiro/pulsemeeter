from pulsemeeter.clients.gtk.adapters.volume_adapter import VolumeAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class VolumeWidget(Gtk.Scale, VolumeAdapter):

    def __init__(self, value: int = 100):


        self.adjustment = Gtk.Adjustment(
            value=value,
            lower=0,
            upper=153,
            step_increment=1,
            page_increment=10
        )

        Gtk.Scale.__init__(
            self,
            hexpand=True,
            adjustment=self.adjustment,
            round_digits=0,
            digits=0,
            width_request=100
        )

        self.add_mark(100, Gtk.PositionType.TOP, '')
        VolumeAdapter.__init__(self)
