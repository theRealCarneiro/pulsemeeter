import gettext

from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class AppBoxWidget(Gtk.Frame):

    app_type: str
    app_box = Gtk.Box()
    apps: dict[int, AppWidget] = {}

    app_label = {
        'sink_input': _('Application Outputs'),
        'source_output': _('Application Inputs')
    }

    def __init__(self, app_type: str):
        super().__init__(margin=5)

        self.app_type = app_type
        self.apps: dict[int, AppWidget] = {}
        app_type_string = self.app_label[app_type]

        title = Gtk.Label(app_type_string, margin=10)

        self.get_accessible().set_name(app_type_string)
        self.set_label_widget(title)
        self.set_label_align(0.5, 0)

        self.app_box = Gtk.VBox()
        self.add(self.app_box)

        self.title = title

    def insert_widget(self, app_widget: AppWidget, app_index: int) -> AppWidget:
        self.apps[app_index] = app_widget
        self.app_box.pack_start(app_widget, False, False, 0)
        return app_widget

    def remove_widget(self, app_index: int) -> AppWidget:
        if app_index not in self.apps:
            return None

        app_widget = self.apps.pop(app_index)
        app_widget.destroy()
        return app_widget
