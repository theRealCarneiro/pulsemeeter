import sys
import subprocess
import threading
import logging
from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib

LOG = logging.getLogger("generic")


class Vumeter(Gtk.ProgressBar):

    def __init__(self, vertical=False):
        super().__init__()
        self.process = None

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

    def listen_peak(self, name, device_type):
        if name == '': return
        dev_type = '0' if device_type == 'vi' or device_type == 'a' else '1'
        command = ['pulse-vumeter', name, dev_type]
        sys.stdout.flush()
        self.process = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            encoding='utf-8',
            universal_newlines=False)

        # return piped values
        for peak in iter(self.process.stdout.readline, ""):
            try:
                peak = float(peak)

            # if pulse crashes, the vumeter will throw an error
            # but we don't want the ui to crash
            except Exception:
                LOG.warning(f'Could not start vumeter for {name}')
                # LOG.debug(traceback.format_exc())
                # continue
                break

            if peak <= 0.00 and self.get_sensitive is True:
                GLib.idle_add(self.set_fraction, 0)
                GLib.idle_add(self.set_sensitive, False)
            else:
                GLib.idle_add(self.set_sensitive, True)
                GLib.idle_add(self.set_fraction, peak)

        # close connection
        self.process.stdout.close()
        self.process.wait()
        # return_code = self.process.wait()

        # if return_code:
            # raise subprocess.CalledProcessError(return_code, command)

    def restart(self, name, device):
        self.close()
        self.reload_device()
        self.start(name, device)

    def reload_device(self):
        self.name = self.config[self.device_type][self.device_id]['name']

    def start(self, name, device_type):
        GLib.idle_add(self.set_sensitive, True)
        self.thread = threading.Thread(target=self.listen_peak, args=(name, device_type))
        self.thread.start()

    def close(self):
        GLib.idle_add(self.set_fraction, 0)
        GLib.idle_add(self.set_sensitive, False)
        if self.process is not None:
            self.process.terminate()
            self.thread.join()
        self.process = None
        self.thread = None
