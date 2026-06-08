import gettext

from pulsemeeter.settings import VERSION

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

_ = gettext.gettext

GITHUB_URL = 'https://github.com/theRealCarneiro/pulsemeeter'
DISCORD_URL = 'https://discord.gg/ekWt9NuEWv'
APP_ICON_NAME = 'Pulsemeeter'
FALLBACK_ICON_NAME = 'multimedia-volume-control'

GUIDE_SECTIONS = [
    (
        _('What is Pulsemeeter?'),
        _('Pulsemeeter is a virtual audio mixer and router built on top of PipeWire. '
          'It lets you create virtual devices and freely route audio between your '
          'inputs and outputs, controlling volume and muting along the way.')
    ),
    (
        _('The four device types'),
        _('<b>Hardware Inputs</b> are physical sources such as microphones and line-in.\n'
          '<b>Virtual Inputs</b> are virtual sinks that applications can play into.\n'
          '<b>Hardware Outputs</b> are physical sinks such as speakers and headphones.\n'
          '<b>Virtual Outputs</b> are virtual sources that applications can capture from.')
    ),
    (
        _('Routing'),
        _('Audio always flows from an input to an output: Hardware and Virtual Inputs '
          'connect to Hardware and Virtual Outputs. Use the connection toggles on each '
          'input device to send its audio to the outputs you want.')
    ),
    (
        _('Cleanup'),
        _('Pulsemeeter has the ability to leave or cleanup the virtual device and routes '
          'it creates with the cleanup setting. If Pulsemeeter is closed, it won\'t be '
          'able to monitor for hotplugging')
    ),
    (
        _('Primary device'),
        _('Marking a device as primary makes it the default that new applications attach '
          'to automatically. This sets the primary in PipeWire itself.')
    ),
    (
        _('VU meters & settings'),
        _('VU meters show the live volume peak of each device. Open the settings menu '
          'to toggle VU meters, enable cleanup on exit, and switch between the available '
          'layouts. Enabling VU Meters will show the inputs "in use" by Pulsemeeter.')
    )
]

FOOTER = _('You can reopen this guide any time from the information button in the settings menu.')


class WelcomeWindow(Gtk.Window):
    '''
    Wwindow introducing Pulsemeeter to new users.
    '''

    def __init__(self, **kwargs):
        super().__init__(title=_('Welcome to Pulsemeeter!'), **kwargs)
        self.set_default_size(560, 640)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                          margin_start=18, margin_end=18, margin_top=18, margin_bottom=18)

        mainbox.append(self._build_header())

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        mainbox.append(separator)

        scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self._build_guide())
        mainbox.append(scrolled)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10,
                             valign=Gtk.Align.END)

        footer = Gtk.Label(halign=Gtk.Align.START, xalign=0, hexpand=True,
                          valign=Gtk.Align.CENTER)
        footer.set_wrap(True)
        footer.set_markup('<span alpha="65%%">%s</span>'
                          % GLib.markup_escape_text(FOOTER))
        footer_box.append(footer)

        close_button = Gtk.Button(label=_('Get started'), valign=Gtk.Align.CENTER)
        close_button.connect('clicked', lambda _: self.close())
        footer_box.append(close_button)

        mainbox.append(footer_box)

        self.set_child(mainbox)

    def _build_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        icon = Gtk.Image.new_from_icon_name(self._resolve_icon_name())
        icon.set_pixel_size(96)
        icon.set_valign(Gtk.Align.CENTER)
        header.append(icon)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                            valign=Gtk.Align.CENTER, hexpand=True)

        title = Gtk.Label(halign=Gtk.Align.START)
        title.set_markup('<span size="xx-large" weight="bold">%s</span>'
                         % GLib.markup_escape_text(_('Welcome to Pulsemeeter!')))
        title_box.append(title)

        version = Gtk.Label(halign=Gtk.Align.START)
        version.set_markup('<span alpha="65%%">%s</span>'
                           % GLib.markup_escape_text(_('Version %s') % VERSION))
        title_box.append(version)

        links = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                        halign=Gtk.Align.START)

        source_link = Gtk.Label()
        source_link.set_markup('<a href="%s">%s</a>'
                               % (GITHUB_URL, GLib.markup_escape_text(_('View Source'))))
        links.append(source_link)

        links.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL,
                                   margin_top=2, margin_bottom=2))

        discord_link = Gtk.Label()
        discord_link.set_markup('<a href="%s">%s</a>'
                                % (DISCORD_URL, GLib.markup_escape_text(_('Discord'))))
        links.append(discord_link)

        title_box.append(links)

        header.append(title_box)
        return header

    def _build_guide(self):
        guide = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14,
                       margin_top=6, margin_bottom=6, margin_start=2, margin_end=2)

        for heading, body in GUIDE_SECTIONS:
            section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            heading_label = Gtk.Label(halign=Gtk.Align.START)
            heading_label.set_markup('<span size="large" weight="bold">%s</span>'
                                     % GLib.markup_escape_text(heading))
            section.append(heading_label)

            body_label = Gtk.Label(halign=Gtk.Align.START, xalign=0)
            body_label.set_wrap(True)
            body_label.set_markup(body)
            section.append(body_label)

            guide.append(section)

        return guide

    @staticmethod
    def _resolve_icon_name():
        '''
        Use the installed themed app icon when available, otherwise fall back to a
        stock icon. (In instances of cloned repo instead of installed)
        '''
        display = Gdk.Display.get_default()
        if display is not None:
            icon_theme = Gtk.IconTheme.get_for_display(display)
            if icon_theme.has_icon(APP_ICON_NAME):
                return APP_ICON_NAME
        return FALLBACK_ICON_NAME
