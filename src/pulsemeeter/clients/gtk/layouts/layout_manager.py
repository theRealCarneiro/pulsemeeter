from pulsemeeter.clients.gtk.widgets.content import Content

from pulsemeeter.clients.gtk.layouts.device.blocks import arrange_widgets as arrange_device_blocks
from pulsemeeter.clients.gtk.layouts.device.bars import arrange_widgets as arrange_device_bars
from pulsemeeter.clients.gtk.layouts.app.blocks import arrange_widgets as arrange_app_blocks
from pulsemeeter.clients.gtk.layouts.app.bars import arrange_widgets as arrange_app_bars
from pulsemeeter.clients.gtk.layouts.content.blocks import arrange_widgets as arrange_content_blocks
from pulsemeeter.clients.gtk.layouts.content.bars import arrange_widgets as arrange_content_bars
from pulsemeeter.clients.gtk.layouts.content.tabbed import arrange_widgets as arrange_content_tabbed

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def get_arrange_device(layout_type: str):
    '''
    Convenience function to get device arrangement function.

    Args:
        layout_type (str): The layout type

    Returns:
        function: The arrangement function
    '''
    layout_functions = {
        'Blocks': arrange_device_blocks,
        'Bars': arrange_device_bars,
        'Tabbed': arrange_device_blocks,
    }

    if layout_type not in layout_functions:
        raise ValueError(f"Unsupported device layout type: {layout_type}")

    return layout_functions[layout_type]


def get_arrange_app(layout_type: str):
    '''
    Convenience function to get device arrangement function.

    Args:
        layout_type (str): The layout type

    Returns:
        function: The arrangement function
    '''
    layout_functions = {
        'Blocks': arrange_app_blocks,
        'Bars': arrange_app_bars,
        'Tabbed': arrange_app_blocks,
    }

    if layout_type not in layout_functions:
        raise ValueError(f"Unsupported device layout type: {layout_type}")

    return layout_functions[layout_type]


def get_arrange_content(layout_type: str):
    '''
    Convenience function to get content arrangement function.

    Args:
        layout_type (str): The layout type

    Returns:
        function: The arrangement function
    '''
    layout_functions = {
        'Blocks': arrange_content_blocks,
        'Bars': arrange_content_bars,
        'Tabbed': arrange_content_tabbed,
    }
    if layout_type not in layout_functions:
        raise ValueError(f"Unsupported content layout type: {layout_type}")
    return layout_functions[layout_type]


def get_layout_list():
    return ['Blocks', 'Bars', 'Tabbed']


if __name__ == '__main__':
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib

    # Create test window
    window = Gtk.Window()
    window.set_title("Widget Test")
    loop = GLib.MainLoop()
    # window.set_default_size(400, 300)

    def loop_quit(_):
        loop.quit()

    window.connect('close-request', loop_quit)

    from pulsemeeter.clients.gtk.widgets.content import Content
    from pulsemeeter.clients.gtk.layouts.content import bars as layout
    from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget

    content_layout = arrange_content('Tabbed')
    content = Content()
    content_layout(content)

    for device_type in ('hi', 'vi', 'a', 'b'):
        content.device_box[device_type].append(VolumeWidget(hexpand=True, vexpand=False))
        content.device_box[device_type].append(VolumeWidget(hexpand=True, vexpand=False))
        content.device_box[device_type].append(VolumeWidget(hexpand=True, vexpand=False))
        content.device_box[device_type].append(VolumeWidget(hexpand=True, vexpand=False))
        content.device_box[device_type].append(VolumeWidget(hexpand=True, vexpand=False))

    # Add widget to window
    window.set_child(content)

    # Show window and run
    window.present()
    loop.run()
