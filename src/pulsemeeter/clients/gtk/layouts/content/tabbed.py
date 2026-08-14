import gettext

from pulsemeeter.model.types import DEVICE_TYPE_PRETTY as PRETTY

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


def _wrap_switcher_labels(switcher):
    child = switcher.get_first_child()
    while child is not None:
        label = child.get_first_child()
        if isinstance(label, Gtk.Label):
            label.set_wrap(True)
            label.set_justify(Gtk.Justification.CENTER)
        child = child.get_next_sibling()


def arrange_widgets(content):
    '''
    Arrange device boxes in a grid layout.

    Args:
        device_boxes (dict): Dictionary of device boxes

    Returns:
        Gtk.Grid: The grid container
    '''
    stack = Gtk.Stack(hexpand=True, vexpand=True)

    content.settings_box.set_vexpand(False)

    # TODO: set box layouts
    for device_type in ('hi', 'vi', 'a', 'b'):
        content.device_box[device_type].set_properties(orientation=Gtk.Orientation.VERTICAL)
        stack.add_titled(content.device_box[device_type], device_type, PRETTY[device_type])

    for app_type in ('sink_input', 'source_output'):
        content.app_box[app_type].set_properties(orientation=Gtk.Orientation.VERTICAL)
        stack.add_titled(content.app_box[app_type], app_type, PRETTY[app_type])

    stack.add_titled(content.settings_box, 'settings', _('Settings'))
    switcher = Gtk.StackSwitcher()
    switcher.set_stack(stack)
    _wrap_switcher_labels(switcher)
    tab_bar = Gtk.ScrolledWindow()
    tab_bar.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
    tab_bar.set_child(switcher)
    tab_bar.set_size_request(-1, 50)

    scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_child(stack)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    main_box.append(tab_bar)  # or just switcher if you don’t need scrolling
    main_box.append(scrolled)

    content.append(main_box)
