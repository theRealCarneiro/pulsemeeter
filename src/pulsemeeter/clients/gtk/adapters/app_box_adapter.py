from pulsemeeter.model.app_model import AppModel
from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget
# from pulsemeeter.clients.gtk.widgets.common.icon_button_widget import IconButton

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class AppBoxAdapter(GObject.GObject):

    app_type: str
    app_box = Gtk.Box()
    apps: dict[str, AppWidget] = {}

    app_label = {
        'sink_input': 'Sink Inputs',
        'source_output': 'Source Outputs'
    }

    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        # self.popover.confirm_button.connect('clicked', self.create_pressed)
        # self.add_app_button.connect('clicked', self.new_app_popup)

    def load_apps(self, apps_schema: dict[str, AppModel]):
        for app_id, app_schema in apps_schema.items():
            self.insert_app(app_schema, app_id)

    def insert_app(self, app_schema: AppModel, app_id: str) -> AppWidget:
        app = AppWidget(app_schema)
        self.app_box.pack_start(app, False, False, 0)
        self.apps[app_id] = app

        return app

    def remove_app(self, app_id: str) -> AppWidget:
        app_widget = self.apps.pop(app_id)
        self.remove(app_widget)
        app_widget.destroy()
        return app_widget
