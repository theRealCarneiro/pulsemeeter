from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def arrange_widgets(app_widget: AppWidget):

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
        'height_request': 200,
        'inverted': True,
    }
    app_widget.set_properties(margin_top=10, margin_bottom=10, margin_start=10, margin_end=10, hexpand=False, vexpand=False)
    app_widget.mute_widget.set_properties(**button_props)
    app_widget.volume_widget.set_properties(**scale_props)
    app_widget.vumeter_widget.set_properties(margin_top=10, margin_start=10, margin_end=0, **scale_props)
    app_widget.combobox.set_hexpand(True)
    # app_widget.icon.set_margin_end(5)

    name_box = Gtk.Box(spacing=4, halign=Gtk.Align.CENTER, margin_bottom=10)
    name_box.append(app_widget.icon)
    name_box.append(app_widget.label)

    # info_box = Gtk.Box(spacing=4, halign=Gtk.Align.CENTER, orientation=Gtk.Orientation.VERTICAL)
    # info_box.append(name_box)
    # info_box.append(app_widget.combobox)

    volume_box = Gtk.Box(spacing=4, halign=Gtk.Align.CENTER, orientation=Gtk.Orientation.VERTICAL)
    volume_box.append(app_widget.volume_widget)
    volume_box.append(app_widget.mute_widget)

    control_grid = Gtk.Grid(hexpand=True, row_spacing=10, column_spacing=10, halign=Gtk.Align.CENTER)
    control_grid.attach(app_widget.vumeter_widget, 0, 1, 1, 1)
    control_grid.attach(volume_box, 1, 1, 1, 1)
    control_grid.attach(app_widget.combobox, 0, 2, 2, 1)

    main_grid = Gtk.Grid(margin_bottom=10, margin_end=10, margin_start=10, hexpand=True, row_spacing=10, column_spacing=10)
    main_grid.attach(name_box, 0, 0, 1, 1)
    main_grid.attach(control_grid, 0, 1, 1, 1)

    app_widget.set_child(main_grid)
