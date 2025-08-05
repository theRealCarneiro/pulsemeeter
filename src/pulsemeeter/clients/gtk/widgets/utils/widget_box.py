# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


class WidgetBox(Gtk.Box):
    '''
    Generic widget container with hash map management.

    This widget provides a simple way to manage dynamic collections of widgets
    with easy add/remove/clear operations and hash map access.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widgets = {}

    def add_widget(self, widget_id, widget):
        '''
        Add a widget to the container.

        Args:
            widget_id (str): Unique identifier for the widget
            widget (Gtk.Widget): The widget to add
        '''
        self.widgets[widget_id] = widget
        self.append(widget)

    def remove_widget(self, widget_id):
        '''
        Remove a widget from the container.

        Args:
            widget_id (str): ID of the widget to remove

        Returns:
            Gtk.Widget: The removed widget, or None if not found
        '''
        if widget_id in self.widgets:
            widget = self.widgets.pop(widget_id)
            self.remove(widget)
            # widget.destroy()
            return widget
        return None

    def get_widget(self, widget_id):
        '''
        Get a widget by its ID.

        Args:
            widget_id (str): ID of the widget to retrieve

        Returns:
            Gtk.Widget: The widget, or None if not found
        '''
        return self.widgets.get(widget_id)

    def has_widget(self, widget_id):
        '''
        Check if a widget exists in the container.

        Args:
            widget_id (str): ID of the widget to check

        Returns:
            bool: True if widget exists, False otherwise
        '''
        return widget_id in self.widgets

    def clear(self):
        '''
        Remove all widgets from the container.
        '''
        for widget in self.widgets.values():
            self.remove(widget)
            # widget.destroy()
        # self.widgets.clear()

    def get_widget_count(self):
        '''
        Get the number of widgets in the container.

        Returns:
            int: Number of widgets
        '''
        return len(self.widgets)

    def get_widget_ids(self):
        '''
        Get all widget IDs in the container.

        Returns:
            list: List of widget IDs
        '''
        return list(self.widgets.keys())

    def get_widgets(self):
        '''
        Get all widgets in the container.

        Returns:
            dict: Dictionary of {id: widget} pairs
        '''
        return self.widgets.copy()

    def update_widget(self, widget_id, widget):
        '''
        Update a widget in the container (remove old, add new).

        Args:
            widget_id (str): ID of the widget to update
            widget (Gtk.Widget): The new widget
        '''
        if widget_id in self.widgets:
            self.remove_widget(widget_id)
        self.add_widget(widget_id, widget)
