import os
from gi import require_version as gi_require_version
gi_require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

class Tray:

    def __init__(self, server):
        # self.ui = None
        self.server = server
        indicator = AppIndicator3.Indicator.new('customtray', 'Pulsmeeter',
              AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        command_one = Gtk.MenuItem(label='Open Pulsmeeter')
        command_one.connect('activate', self.open_ui)
        exittray = Gtk.MenuItem(label='Close')
        exittray.connect('activate', self.quit)

        menu = Gtk.Menu()
        menu.append(command_one)
        menu.append(exittray)
        menu.show_all()

        indicator.set_menu(menu)
        self.indicator = indicator

    def quit(self, widget=None):
        self.server.handle_exit_signal()

    def close(self):
        Gtk.main_quit()

    def open_ui(self):
        os.popen('pulsemeeter')
