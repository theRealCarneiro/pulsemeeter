from pulsemeeter.clients.gtk.layouts.device.blocks import arrange_widgets as arrange_device_blocks
from pulsemeeter.clients.gtk.layouts.device.bars import arrange_widgets as arrange_device_bars
from pulsemeeter.clients.gtk.layouts.app.blocks import arrange_widgets as arrange_app_blocks
from pulsemeeter.clients.gtk.layouts.app.bars import arrange_widgets as arrange_app_bars
from pulsemeeter.clients.gtk.layouts.content.blocks import arrange_widgets as arrange_content_blocks
from pulsemeeter.clients.gtk.layouts.content.bars import arrange_widgets as arrange_content_bars
from pulsemeeter.clients.gtk.layouts.content.tabbed import arrange_widgets as arrange_content_tabbed


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
