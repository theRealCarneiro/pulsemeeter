import logging
import math

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")

DB_FLOOR = -50.0


class VumeterWidget(Gtk.ProgressBar):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    async def update_peak(self, peak):
        if peak <= 0.00:
            GLib.idle_add(self.set_fraction, 0)
            GLib.idle_add(self.set_sensitive, False)
        else:
            db = 20.0 * math.log10(peak)
            fraction = max(0.0, min(1.0, (db - DB_FLOOR) / -DB_FLOOR))
            GLib.idle_add(self.set_sensitive, True)
            GLib.idle_add(self.set_fraction, fraction)
