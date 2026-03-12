import gettext

from pulsemeeter.model.types import DEVICE_TYPE_PRETTY as PRETTY
# from pulsemeeter.clients.gtk.widgets.utils.framed_widget import FramedWidget
# from pulsemeeter.clients.gtk.widgets.content import Content

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceBox(Gtk.Frame):

    def __init__(self, widget, label, button=None):
        '''
        Returns a framed widget with the requested label
            "widget" is the widget that is going to be framed
            "label" is the label of the frame
        '''
        super().__init__(margin_bottom=5, margin_top=5, margin_start=5, margin_end=5)
        title = Gtk.Label(label=label, margin_bottom=5, halign=Gtk.Align.CENTER)
        main_box = Gtk.Box(hexpand=True, spacing=10)
        main_box.append(title)
        if button is not None:
            main_box.append(button)

        self.set_label_widget(main_box)
        self.set_label_align(0.5)
        self.set_child(widget)


def arrange_widgets(content):
    '''
    Arrange device boxes in a grid layout.

    Args:
        device_boxes (dict): Dictionary of device boxes

    Returns:
        Gtk.Grid: The grid container
    '''
    grid = Gtk.Grid(margin_start=10, margin_end=10, margin_top=10, margin_bottom=10, hexpand=True)

    for device_type in ('hi', 'vi', 'a', 'b'):
        content.device_box[device_type].set_properties(orientation=Gtk.Orientation.HORIZONTAL)

    for app_type in ('sink_input', 'source_output'):
        content.app_box[app_type].set_properties(orientation=Gtk.Orientation.HORIZONTAL)

    device_frame = {'a': None, 'b': None, 'vi': None, 'hi': None}
    for device_type in device_frame:
        device_frame[device_type] = DeviceBox(
            content.device_box[device_type],
            PRETTY[device_type],
            content.create_device_button[device_type]
        )

    # id rather use framed
    grid.attach(device_frame['hi'], 0, 0, 1, 1)
    grid.attach(device_frame['vi'], 1, 0, 1, 1)
    grid.attach(device_frame['a'], 0, 1, 1, 1)
    grid.attach(device_frame['b'], 1, 1, 1, 1)
    grid.attach(DeviceBox(content.app_box['sink_input'], PRETTY['sink_input']), 2, 0, 1, 1)
    grid.attach(DeviceBox(content.app_box['source_output'], PRETTY['source_output']), 2, 1, 1, 1)

    settings_popover = Gtk.Popover()
    settings_popover.set_child(content.settings_box)
    content.settings_button.set_popover(settings_popover)
    content.settings_box.set_properties(margin_start=10, margin_end=10, margin_top=10, margin_bottom=10)

    settings_box = Gtk.Box(halign=Gtk.Align.END, valign=Gtk.Align.START, vexpand=False,
                           margin_top=6, margin_end=6)
    settings_box.append(content.settings_button)

    scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
    scrolled.set_child(grid)

    mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    mainbox.append(settings_box)
    mainbox.append(scrolled)

    content.append(mainbox)
