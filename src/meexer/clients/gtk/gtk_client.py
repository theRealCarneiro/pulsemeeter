import asyncio
import threading

from meexer.model.config_model import ConfigModel
from meexer.model.app_manager_model import AppManagerModel
# from meexer.schemas.app_schema import AppModel

# from meexer.clients.gtk.widgets.app.app_widget import AppWidget, AppCombobox
# from meexer.clients.gtk.widgets.device.create_device_widget import VirtualDevicePopup, HardwareDevicePopup
from meexer.clients.gtk.adapters.application_adapter import ApplicationAdapter
from meexer.settings import STYLE_FILE

# pylint: disable=wrong-import-order,wrong-import-position
from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class GtkClient(Gtk.Application, ApplicationAdapter):

    def __init__(self):
        Gtk.Application.__init__(self, application_id='org.pulsemeeter.meexer')
        ApplicationAdapter.__init__(self)
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(STYLE_FILE)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.window = None

        # create client and get config
        # self.client = Client(subscription_flags=0, instance_name='gtk')
        # res = self.client.send_request('get_config', {})
        # self.config = ConfigModel(**res.data)
        # self.client_subscribe = Client(subscription_flags=1, instance_name='gtk_callback')
        self.config_model = ConfigModel.load_config()
        self.app_manager = AppManagerModel()

        # create vumeter loop thread
        self.vumeter_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.vumeter_thread = threading.Thread(target=self.vumeter_loop.run_forever, daemon=True)
        self.vumeter_thread.start()

        self.vumeter_tasks = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}, 'sink_input': {}, 'source_output': {}}
        self.device_handlers = {'a': {}, 'b': {}, 'vi': {}, 'hi': {}}
        self.app_handlers = {'sink_input': {}, 'source_output': {}}

    def do_activate(self, *args, **kwargs):

        if self.window is None:
            self.create_window()

        # self.window.connect('destroy', self.on_shutdown)
        self.window.show_all()
        self.window.present()

    # def on_shutdown(self, _):
    #     self.config_model.device_manager.cleanup()
