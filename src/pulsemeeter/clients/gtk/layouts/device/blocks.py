from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def arrange_widgets(device_widget: DeviceWidget):
    '''
    Arrange device widget in blocks layout.

    Args:
        device_widget: The device widget to arrange

    Returns:
        DeviceWidget: The arranged device widget
    '''

    # Create grid layout
    button_props = {
        'vexpand': False,
        'hexpand': False,
        'valign': Gtk.Align.CENTER,
        'halign': Gtk.Align.END
    }

    device_widget.edit_button.set_properties(halign=Gtk.Align.END, hexpand=True)
    device_widget.primary_widget.set_properties(**button_props)
    device_widget.mute_widget.set_properties(**button_props)
    device_widget.vumeter_widget.set_properties(margin_bottom=10, margin_start=10, hexpand=True)
    device_widget.volume_widget.set_properties(hexpand=True)

    device_widget.set_properties(margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)

    main_grid = Gtk.Grid(hexpand=False, width_request=300, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
    control_grid = Gtk.Grid(hexpand=True)

    name_container = Gtk.Box(margin_start=0, margin_end=0, hexpand=True, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    name_container.append(device_widget.nick_label)
    name_container.append(device_widget.description_label)
    # name_container.append(Gtk.Box(hexpand=True))
    name_container.append(device_widget.edit_button)
    if device_widget.device_model.nick == device_widget.device_model.description:
        device_widget.description_label.set_visible(False)

    # device_widget.set_label_widget(name_container)
    # device_widget.set_label_align(0.5)

    control_grid.attach(device_widget.volume_widget, 0, 0, 1, 1)
    control_grid.attach(device_widget.vumeter_widget, 0, 1, 2, 1)
    button_box = Gtk.Box()
    button_box.append(device_widget.mute_widget)
    if device_widget.device_model.primary is not None:
        button_box.append(device_widget.primary_widget)

    main_grid.attach(name_container, 0, 0, 1, 1)
    control_grid.attach(button_box, 1, 0, 1, 1)
    main_grid.attach(control_grid, 0, 1, 1, 1)

    if device_widget.device_model.get_type() in ('vi', 'hi'):
        connections_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        connections_container.append(device_widget.connections_widgets['a'])
        connections_container.append(device_widget.connections_widgets['b'])
        main_grid.attach(connections_container, 0, 2, 1, 1)

    device_widget.set_child(main_grid)
    return device_widget
