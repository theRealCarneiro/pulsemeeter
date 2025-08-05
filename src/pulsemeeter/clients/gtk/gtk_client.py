''' 
GTK Application client for PulseMeeter.
Manages application lifecycle, system tray, and delegates UI logic to GtkController.
'''
import logging

from pulsemeeter.settings import CONFIG_FILE
from pulsemeeter.model.config_model import ConfigModel

# from pulsemeeter.clients.gtk.widgets.indicator import Tray
# from pulsemeeter.settings import STYLE_FILE

from pulsemeeter.utils.config_persistence import ConfigPersistence
from pulsemeeter.repository.device_repository import DeviceRepository
from pulsemeeter.controller.gtk_controller import GtkController
from pulsemeeter.controller.app_controller import AppController
from pulsemeeter.controller.device_controller import DeviceController
from pulsemeeter.controller.event_controller import EventController

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '4.0')
# gi_require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")


class GtkClient(Gtk.Application):
    '''
    GTK Application client for PulseMeeter.
    Manages the application lifecycle, system tray indicator, and delegates UI logic to GtkController.
    Attributes:
        window (Gtk.Window): The main application window.
        config_model (ConfigModel): The configuration model instance.
    '''

    def __init__(self):
        '''
        Initialize the GtkClient application.
        '''
        super().__init__(application_id='org.pulsemeeter.pulsemeeter')
        self.window = None
        self.indicator = None

        self.config_persistence = ConfigPersistence(ConfigModel, CONFIG_FILE)
        self.device_repository = DeviceRepository(self.config_persistence)
        self.event_controller = EventController(device_repository=self.device_repository)
        self.device_controller = DeviceController(device_repository=self.device_repository)
        self.gtk_controller = GtkController(device_repository=self.device_repository)
        self.app_controller = AppController()

        # create vumeter loop thread
        self.config_model = self.config_persistence.get_config()
        self.gtk_controller_handlers = {}
        self.event_controller_handlers = {}
        self.device_controller_handlers = {}
        self.connect('shutdown', self.on_shutdown)

    # def load_css(self):
        # style_provider = Gtk.CssProvider()
        # style_provider.load_from_path(STYLE_FILE)
        # Gtk.StyleContext.add_provider_for_screen(
        #     Gdk.Screen.get_default(),
        #     style_provider,
        #     Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        # )

    def do_activate(self, *args, **kwargs):
        '''
        Called when the Application starts.
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        '''
        if self.config_model.tray:
            self.hold()

        self.window = self.gtk_controller.create_window(self)
        # self.indicator = self.create_indicator()
        self.window.present()
        # self.window.connect('close-request', self.on_window_destroy)

        self.connect_gtk_controller_events()
        self.connect_device_controller_events()
        self.connect_event_controller_events()

        self.event_controller.start_listen()

    def on_shutdown(self, *_):
        '''
        Called when the Application quits (different from window destroy).
        Args:
            *_: Additional positional arguments.
        '''
        if self.config_model.cleanup is True:
            self.device_controller.cleanup()

        self.config_persistence.save()
        self.event_controller.stop_listen()

    def on_window_destroy(self, _):
        self.block_event_controller_events()

    # def create_indicator(self):
    #     '''
    #     Create and configure the system tray indicator.
    #     Returns:
    #         Tray: The created tray indicator instance.
    #     '''
    #     indicator = Tray(self)  # Pass the application instance
    #     indicator.set_active(self.config_model.tray)
    #     indicator.connect('quit', self.tray_exit)
    #     indicator.connect('create_window', self.tray_show)
    #     return indicator

    def tray_exit(self, _):
        '''
        Called by the tray to close the application.
        Args:
            _: The triggering event or widget (unused).
        '''
        self.release()
        self.quit()

    def tray_show(self, _):
        '''
        Called by the tray to show the application window.
        Args:
            _: The triggering event or widget (unused).
        '''
        self.window = self.gtk_controller.create_window(self)
        self.window.present()
        self.unblock_event_controller_events()
        self.window.connect('close-request', self.on_window_destroy)

    def connect_gtk_controller_events(self):
        signal_map = {
            'volume': self.device_controller.set_volume,
            'mute': self.device_controller.set_mute,
            'primary': self.device_controller.set_primary,
            'connect': self.device_controller.set_connection,
            'connection_change': self.device_controller.update_connection,
            'device_new': self.device_controller.create_device,
            'device_remove': self.device_controller.remove_device,
            'device_change': self.device_controller.update_device,
            'app_volume': self.app_controller.set_volume,
            'app_mute': self.app_controller.set_mute,
            'app_device': self.app_controller.change_device,
        }

        for signal_name, callback in signal_map.items():
            self.gtk_controller_handlers[signal_name] = self.gtk_controller.connect(signal_name, callback)

    def connect_device_controller_events(self):
        signal_map = {
            'device_new': self.gtk_controller.device_new_callback,
            'device_remove': self.gtk_controller.device_remove_callback,
            'device_change': self.gtk_controller.device_change_callback,
        }

        for signal_name, callback in signal_map.items():
            self.device_controller_handlers[signal_name] = self.device_controller.connect(signal_name, callback)

    def connect_event_controller_events(self):
        signal_map = {
            'pa_device_change': self.gtk_controller.pa_device_change_callback,
            'pa_primary_change': self.gtk_controller.pa_primary_change_callback,
            'pa_app_change': self.gtk_controller.app_change_callback,
            'pa_app_new': self.gtk_controller.app_new_callback,
            'pa_app_remove': self.gtk_controller.app_remove_callback,
        }

        for signal_name, callback in signal_map.items():
            self.event_controller_handlers[signal_name] = self.event_controller.connect(signal_name, callback)

    def block_event_controller_events(self):
        for signal_name in self.event_controller_handlers:
            index = self.event_controller_handlers[signal_name]
            self.event_controller.block(signal_name, index)

    def unblock_event_controller_events(self):
        for signal_name in self.event_controller_handlers:
            index = self.event_controller_handlers[signal_name]
            self.event_controller.unblock(signal_name, index)
