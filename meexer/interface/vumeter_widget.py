import logging
import asyncio
import pulsectl_asyncio
from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib

LOG = logging.getLogger("generic")


class Vumeter(Gtk.ProgressBar):

    def __init__(self, name, vertical=False):
        super().__init__()
        self.name = name
        self.thread = None

        if vertical:
            self.set_orientation(Gtk.Orientation.VERTICAL)
            self.set_margin_bottom(8)
            self.set_margin_top(8)
            self.set_halign(Gtk.Align.CENTER)
            self.set_inverted(True)
        else:
            self.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.set_margin_start(8)
            self.set_margin_end(8)
            self.set_margin_top(8)

        self.set_vexpand(True)
        self.set_hexpand(True)

    async def _listen_peak(self):
        async with pulsectl_asyncio.PulseAsync(f'{self.name}_peak') as pulse:
            async for peak in pulse.subscribe_peak_sample(self.name, rate=24):
                await self._update_peak(peak)

    async def _update_peak(self, peak):
        if peak <= 0.00 and self.get_sensitive is True:
            GLib.idle_add(self.set_fraction, 0)
            GLib.idle_add(self.set_sensitive, False)
        else:
            GLib.idle_add(self.set_sensitive, True)
            GLib.idle_add(self.set_fraction, peak)

    def restart(self):
        self.close()
        self.start()

    # def run_task(self):
    def start(self):
        GLib.idle_add(self.set_sensitive, True)
        self.async_loop = asyncio.get_event_loop()
        self.peak_task = asyncio.run_coroutine_threadsafe(self._listen_peak(), self.async_loop)

    def close(self):
        GLib.idle_add(self.set_fraction, 0)
        GLib.idle_add(self.set_sensitive, False)
        self.thread = None
