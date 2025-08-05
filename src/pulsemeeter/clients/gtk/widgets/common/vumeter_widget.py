import logging

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")


class VumeterWidget(Gtk.ProgressBar):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
            # orientation=Gtk.Orientation.HORIZONTAL,
            # margin_bottom=8,
            # margin_top=8,
            # margin_start=10,
            # margin_end=8,
            # width_request=100,
            # hexpand=True
        # )

    async def update_peak(self, peak):
        if peak <= 0.00 and self.get_sensitive() is True:
            GLib.idle_add(self.set_fraction, 0)
            GLib.idle_add(self.set_sensitive, False)
        else:
            GLib.idle_add(self.set_sensitive, True)
            GLib.idle_add(self.set_fraction, peak)
