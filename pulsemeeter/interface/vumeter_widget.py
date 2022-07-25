import sys
import subprocess
import threading
import logging
import traceback
from gi import require_version as gi_require_version

gi_require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib

LOG = logging.getLogger("generic")


class Vumeter(Gtk.ProgressBar):

    def __init__(self, device_type, device_id, config, vertical=True):
        super(Vumeter, self).__init__()

        self.device_type = device_type
        self.device_id = device_id
        self.config = config
        self.name = config[device_type][device_id]['name']
        self.process = None

        if vertical and device_type not in ['a', 'b']:
            self.set_orientation(Gtk.Orientation.VERTICAL)
            self.set_margin_bottom(8)
            self.set_margin_top(8)
            self.set_halign(Gtk.Align.CENTER)
            self.set_inverted(True)
        else:
            self.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.set_margin_start(8)
            self.set_margin_end(8)

        self.set_vexpand(True)
        self.set_hexpand(True)

    def listen_peak(self):
        if self.name == '': return
        dev_type = '0' if self.device_type == 'vi' or self.device_type == 'a' else '1'
        command = ['pulse-vumeter', self.name, dev_type]
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
            except Exception as ex:
                LOG.warning(f'Could not start vumeter for {self.name}')
                LOG.debug(traceback.format_exc())
                continue
                # break

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

    def restart(self):
        self.close()
        self.reload_device()
        self.start()

    def reload_device(self):
        self.name = self.config[self.device_type][self.device_id]['name']

    def start(self):
        GLib.idle_add(self.set_sensitive, True)
        self.thread = threading.Thread(target=self.listen_peak)
        self.thread.start()

    def close(self):
        GLib.idle_add(self.set_fraction, 0)
        GLib.idle_add(self.set_sensitive, False)
        if self.process is not None:
            self.process.terminate()
            self.thread.join()
        self.process = None
        self.thread = None
