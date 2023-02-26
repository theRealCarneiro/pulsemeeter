from meexer.ipc.client import Client
from meexer.schemas import requests_schema
from meexer.schemas.app_schema import AppSchema
from gi.repository import Gtk

CLIENT = Client.get_client('gtk')

'''
This module is for implementing the gtk signal callback for apps and making the requests
to the server
'''


def volume(scale: Gtk.Scale, app: AppSchema, volume: int):
    data = {
        'app': app.__dict__,
        'volume': volume
    }

    requests_schema.AppVolume(**data)
    CLIENT.send_request('app_volume', data)


def move(combobox: Gtk.ComboBox, app: AppSchema):
    data = {
        'app': app.__dict__,
        'device': combobox.get_active_text()
    }

    requests_schema.AppVolume(**data)
    CLIENT.send_request('app_volume', data)


# TODO
def mute():
    pass
