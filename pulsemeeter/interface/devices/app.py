from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import logging


LOG = logging.getLogger("generic")


class App(Gtk.VBox):

    def __init__(self, id, label, icon, volume, device, dev_list):
        super(App, self).__init__(spacing=0)
        icon = Gio.ThemedIcon(name=icon)
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        image.set_margin_left(10)

        label = Gtk.Label(label)
        label.props.halign = Gtk.Align.START

        combobox = Gtk.ComboBoxText()
        combobox.props.halign = Gtk.Align.END
        combobox.set_hexpand(True)
        combobox.set_margin_right(10)

        for dev in dev_list:
            combobox.append_text(dev)
        try:
            index = dev_list.index(device)
        except Exception:
            index = 0
        combobox.set_active(index)
        # combobox.connect('changed', self.app_combo_change, id)

        print(volume)
        value = int(volume)
        adjust = Gtk.Adjustment(lower=0, upper=153, step_increment=1, page_increment=10)
        adjust.set_value(value)
        # adjust.connect('value_changed', self.volume_change, id, dev_type)

        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjust)
        scale.set_hexpand(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_digits(0)
        scale.add_mark(100, Gtk.PositionType.BOTTOM, '')
        scale.set_margin_left(10)
        scale.set_size_request(300, -1)

        separator_top = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator_top.set_margin_bottom(5)
        separator_bottom = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator_bottom.set_margin_top(5)

        box = Gtk.Box(spacing=5)
        box.pack_start(image, expand=False, fill=False, padding=0)
        box.pack_start(label, expand=False, fill=False, padding=0)
        box.pack_start(combobox, expand=False, fill=True, padding=0)

        self.label = label
        self.icon = icon
        self.combobox = combobox
        self.adjust = adjust
        self.volume = scale

        self.set_valign(Gtk.Align.START)
        self.pack_start(separator_top, expand=False, fill=False, padding=0)
        self.pack_start(box, expand=False, fill=False, padding=0)
        self.pack_start(scale, expand=False, fill=False, padding=0)
        self.pack_start(separator_bottom, expand=False, fill=False, padding=0)
