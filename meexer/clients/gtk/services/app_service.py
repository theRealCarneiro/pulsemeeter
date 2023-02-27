from gi.repository import Gtk
from meexer.ipc.client import Client
from meexer.schemas import requests_schema
# from meexer.schemas.app_schema import AppSchema

CLIENT_NAME = 'gtk'

'''
This module is for implementing the gtk signal callback for apps and making the
requests to the server
'''


def volume(scale: Gtk.Scale, app_type: str, app_index: int):
    data = {
        'app_type': app_type,
        'app_index': app_index,
        'volume': scale.get_value()
    }

    requests_schema.AppVolume(**data)
    Client.get_client(CLIENT_NAME).send_request('app_volume', data)


def mute(button: Gtk.ToggleButton, app_type: str, app_index: int):
    data = {
        'app_type': app_type,
        'app_index': app_index,
        'state': button.get_active()
    }

    requests_schema.AppMute(**data)
    Client.get_client(CLIENT_NAME).send_request('app_mute', data)


def move(combobox: Gtk.ComboBox, app_type: str, app_index: int):
    data = {
        'app_type': app_type,
        'app_index': app_index,
        'device': combobox.get_active_text(app_type)
    }

    requests_schema.AppMove(**data)
    Client.get_client(CLIENT_NAME).send_request('app_move', data)
