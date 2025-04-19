from pulsemeeter.model.app_model import AppModel
from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget
from pulsemeeter.clients.gtk.widgets.app.app_combobox import AppCombobox
from pulsemeeter.clients.gtk.adapters.app_box_adapter import AppBoxAdapter

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class AppBoxWidget(Gtk.Frame, AppBoxAdapter):

    app_label = {
        'sink_input': 'Application Outputs',
        'source_output': 'Application Inputs'
    }

    def __init__(self, app_type: str, app_manager):
        Gtk.Frame.__init__(self, margin=5)

        self.app_type = app_type
        self.apps: dict[str, AppWidget] = {}
        app_type_string = self.app_label[app_type]

        title = Gtk.Label(app_type_string, margin=10)

        self.get_accessible().set_name(app_type_string)
        self.set_label_widget(title)
        self.set_label_align(0.5, 0)

        self.app_box = Gtk.VBox()
        self.add(self.app_box)

        self.title = title

        AppBoxAdapter.__init__(self, app_manager=app_manager)

        apps_schema = app_manager.__dict__[app_type]
        self.load_apps(apps_schema)
