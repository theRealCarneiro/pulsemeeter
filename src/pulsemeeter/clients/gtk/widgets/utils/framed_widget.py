import gettext

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class FramedWidget(Gtk.Frame):

    def __init__(self, widget, label):
        '''
        Returns a framed widget with the requested label
            "widget" is the widget that is going to be framed
            "label" is the label of the frame
        '''
        super().__init__(margin_bottom=5, margin_top=5, margin_start=5, margin_end=5)
        title = Gtk.Label(label=label, margin_bottom=5)
        self.set_label_widget(title)
        self.set_label_align(0.5)
        self.set_child(widget)
