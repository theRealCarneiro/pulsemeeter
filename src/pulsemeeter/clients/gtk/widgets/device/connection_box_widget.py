import gettext

from pulsemeeter.clients.gtk.adapters.connection_box_adapter import ConnectionBoxAdapter
from pulsemeeter.clients.gtk.widgets.device.connection_widget import ConnectionWidget
from pulsemeeter.model.connection_model import ConnectionModel

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Atk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionBoxWidget(Gtk.Box, ConnectionBoxAdapter):

    # gtk wont allow to have this declaration only on parent
    __gsignals__ = {
        "connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, bool)),
        "update_connection": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str, str, GObject.TYPE_PYOBJECT))
    }

    def __init__(self, output_type, connections_schemas: dict[str, dict[str, ConnectionModel]]):
        self.model = connections_schemas
        Gtk.Box.__init__(self)
        ConnectionBoxAdapter.__init__(self)
        self.a = Gtk.Box()
        self.b = Gtk.Box()
        self.a.get_accessible().set_name(_('Hardware Output connection box'))
        self.a.get_accessible().set_role(Atk.Role.PANEL)
        self.b.get_accessible().set_name(_('Hardware Input connection box'))
        self.b.get_accessible().set_role(Atk.Role.PANEL)
        self.add(self.a)
        self.add(self.b)

        self.output_type = output_type
        if connections_schemas is not None:
            self.load_widgets(connections_schemas)
