from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import logging


LOG = logging.getLogger("generic")


class App(Gtk.VBox):

    def __init__(self, client, aid, label, icon, volume, device, device_type):
        self.client = client
        self.id = aid
        self.label = label
        self.icon = icon
        self.volume = volume
        self.device = device
        self.device_type = device_type

        super().__init__(spacing=0)
        icon = Gio.ThemedIcon(name=icon)
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        image.set_margin_left(10)

        label = Gtk.Label(label)
        label.props.halign = Gtk.Align.START

        combobox = Gtk.ComboBoxText()
        combobox.props.halign = Gtk.Align.END
        combobox.set_hexpand(True)
        combobox.set_margin_right(10)

        devices_config = client.config['vi' if device_type == 'sink-inputs' else 'b']
        dev_list = [item['name'] for key, item in devices_config.items()]

        for dev in dev_list:
            combobox.append_text(dev)
        try:
            index = dev_list.index(device)
        except Exception:
            index = 0
        combobox.set_active(index)
        self.combobox = combobox

        print(volume)
        value = int(volume)
        adjust = Gtk.Adjustment(lower=0, upper=153, step_increment=1, page_increment=10)
        adjust.set_value(value)

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

        self.combobox.connect('changed', self.combo_change)
        self.adjust.connect('value_changed', self.volume_change)

    def combo_change(self, combobox):
        """
        Gets called whenever a new device gets selected in the combobox
        """
        name = combobox.get_active_text()
        self.client.move_app_device(self.id, name, self.device_type[:-1])

    def volume_change(self, slider):
        """
        Gets called whenever an app volume slider changes
        """
        val = slider.get_value()
        self.client.set_app_volume(self.id, int(val), self.device_type[:-1])
