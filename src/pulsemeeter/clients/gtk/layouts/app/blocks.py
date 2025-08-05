from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def _set_properties(app_widget: AppWidget):
    button_props = {
        'vexpand': False,
        'hexpand': False,
        'valign': Gtk.Align.CENTER,
        'halign': Gtk.Align.CENTER
    }

    scale_props = {
        'orientation': Gtk.Orientation.HORIZONTAL,
        'vexpand': False,
        'hexpand': True,
        # 'width_request': 200,
    }
    app_widget.set_properties(margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
    app_widget.mute_widget.set_properties(**button_props, margin_bottom=10)
    app_widget.volume_widget.set_properties(**scale_props)
    app_widget.vumeter_widget.set_properties(margin_start=10, **scale_props)
    app_widget.combobox.set_properties(
        hexpand=True,
        halign=Gtk.Align.END,
        margin_bottom=10
    )
    app_widget.icon.set_margin_end(5)


def arrange_widgets(app_widget: AppWidget):
    _set_properties(app_widget)

    main_grid = Gtk.Grid(margin_bottom=10, margin_end=10, margin_start=10, hexpand=True)
    info_grid = Gtk.Grid(margin_start=8, hexpand=True)
    control_grid = Gtk.Grid(hexpand=True)

    main_grid.attach(info_grid, 0, 0, 1, 1)
    main_grid.attach(control_grid, 0, 1, 1, 1)

    info_grid.attach(app_widget.icon, 0, 0, 1, 1)
    info_grid.attach(app_widget.label, 1, 0, 1, 1)
    info_grid.attach(app_widget.combobox, 2, 0, 1, 1)

    control_grid.attach(app_widget.volume_widget, 0, 0, 1, 1)
    control_grid.attach(app_widget.mute_widget, 1, 0, 1, 1)
    control_grid.attach(app_widget.vumeter_widget, 0, 1, 2, 1)

    app_widget.set_child(main_grid)
