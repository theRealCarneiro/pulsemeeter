from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def _set_properties(device_widget: DeviceWidget):
    button_props = {
        'vexpand': False,
        'hexpand': False,
        'valign': Gtk.Align.CENTER,
        'halign': Gtk.Align.CENTER
    }

    scale_props = {
        'orientation': Gtk.Orientation.VERTICAL,
        'vexpand': True,
        'hexpand': False,
        'inverted': True,
        'height_request': 200,
    }

    device_widget.edit_button.set_properties(**button_props)
    device_widget.primary_widget.set_properties(**button_props)
    device_widget.mute_widget.set_properties(**button_props)
    device_widget.volume_widget.set_properties(**scale_props)
    device_widget.vumeter_widget.set_properties(margin_start=10, **scale_props)
    if device_widget.device_model.get_type() in ['vi', 'hi']:
        device_widget.connections_widgets['a'].set_properties(orientation=Gtk.Orientation.VERTICAL)
        device_widget.connections_widgets['b'].set_properties(orientation=Gtk.Orientation.VERTICAL)

    device_widget.set_properties(margin_top=10, margin_bottom=10, margin_start=10, margin_end=10, hexpand=False, vexpand=False)
    device_widget.description_label.set_properties(
        ellipsize=Pango.EllipsizeMode.END,
        max_width_chars=12,
    )

    # if nick == description, don't show description
    if device_widget.device_model.nick == device_widget.device_model.description:
        device_widget.description_label.set_visible(False)


def arrange_widgets(device_widget: DeviceWidget):
    '''
    Arrange device widget in bars layout.

    Args:
        device_widget: The device widget to arrange

    Returns:
        DeviceWidget: The arranged device widget
    '''
    _set_properties(device_widget)

    name_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5, halign=Gtk.Align.CENTER)
    name_container.append(device_widget.nick_label)
    name_container.append(device_widget.edit_button)

    title_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, halign=Gtk.Align.CENTER)
    title_container.append(name_container)
    title_container.append(device_widget.description_label)

    device_widget.set_label_widget(title_container)
    device_widget.set_label_align(0.5)

    main_container = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        halign=Gtk.Align.CENTER,
        spacing=10,
        margin_top=10,
        margin_bottom=10,
        margin_start=10,
        margin_end=10
    )

    primary = device_widget.device_model.primary
    device_widget.vumeter_widget.set_vexpand(True)
    control_grid = Gtk.Grid(row_spacing=0, column_spacing=0)
    control_grid.attach(device_widget.vumeter_widget, 0, 0, 1, 2)
    control_grid.attach(device_widget.volume_widget, 1, 0, 1, 1)

    button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    button_box.append(device_widget.mute_widget)
    if primary is not None:
        button_box.append(device_widget.primary_widget)
    control_grid.attach(button_box, 1, 1, 1, 1)

    main_container.append(control_grid)

    if device_widget.device_model.get_type() in ('vi', 'hi'):
        connections_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        connections_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        connections_container.append(device_widget.connections_widgets['a'])
        connections_container.append(device_widget.connections_widgets['b'])
        connections_box.append(connections_container)
        # volume_container.append(connections_box)
        main_container.append(connections_box)


    device_widget.set_child(main_container)
    return device_widget
