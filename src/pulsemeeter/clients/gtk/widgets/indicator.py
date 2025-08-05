# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '4.0')
# gi_require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GObject, AyatanaAppIndicator3  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class Tray(GObject.GObject):

    __gsignals__ = {
        'create_window': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
        'quit': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self):
        super().__init__()
        self.indicator = self.create_indicator()
        # self.set_active(True)

    def create_indicator(self):

        indicator = AyatanaAppIndicator3.Indicator.new(
            'Pulsemeeter',
            'Pulsemeeter',
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        menu = self.build_tray_menu()
        indicator.set_menu(menu)

        return indicator

    def set_active(self, status: bool):
        if status is True:
            self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
            return

        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE)

    def build_tray_menu(self):
        menu = Gtk.Menu()

        show_item = Gtk.MenuItem(label='Show')
        show_item.connect('activate', self.create_window)
        menu.append(show_item)

        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect('activate', self.quit_application)
        menu.append(quit_item)

        return menu

    def create_window(self, _):
        self.emit('create_window')

    def quit_application(self, _):
        self.emit('quit')
