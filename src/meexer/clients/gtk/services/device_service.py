from meexer.ipc.client import Client
from meexer.clients.gtk.widgets.common import CHANNEL_MAPS
# from meexer.schemas.ipc_schema import SubscriptionFlags

from meexer.schemas import requests_schema, ipc_schema

CLIENT_NAME = 'gtk'


'''
This module is for implementing the gtk signal callback for devices and making the requests
to the server
'''


def create(_, popover, device_type_abstract, device_list):
    '''
    Called when the create button is pressed
    '''

    if device_type_abstract in ('b', 'vi'):
        nick_text = popover.name.get_option()
        channel_map = popover.channel_map.combobox.get_active_text()
        channel_list = CHANNEL_MAPS[channel_map]
        selected_channels = [True for _ in channel_list]

    else:
        nick_text = popover.name.get_option()
        selected_device = popover.device.combobox.get_active()
        channel_list = device_list[selected_device]['channel_list']
        selected_channels = popover.ports.get_selected()

    # device_text = self.device.get_active_text() or ""
    ports_data = [0, 1]
    # ports_data = self.ports.get_selected_channels()  # e.g., [0, 1]
    channels = len(ports_data) if ports_data else 2
    device_type = 'sink' if device_type_abstract in ('a', 'vi') else 'source'
    device_class = 'virtual' if device_type_abstract in ('b', 'vi') else 'hardware'

    data = {
        'device': {
            'name': nick_text,
            'channels': channels,
            'channel_list': channel_list,
            'selected_channels': selected_channels,
            'device_type': device_type,
            'device_class': device_class
        }
    }

    Client.get_client(CLIENT_NAME).send_request('create_device', data)


def connect(button, input_type, input_id, output_type, output_id):
    '''
    Called when the connect button is toggled
    '''
    data = {
        'source': {
            'device_type': input_type,
            'device_id': input_id
        },
        'output': {
            'device_type': output_type,
            'device_id': output_id
        },
        'state': button.get_active()
    }

    requests_schema.Connect(**data)
    Client.get_client(CLIENT_NAME).send_request('connect', data)


def mute(button, device_type, device_id):
    '''
    Called when the mute button is toggled
    '''

    data = {
        'index': {
            'device_type': device_type,
            'device_id': device_id
        },
        'state': button.get_active()
    }

    requests_schema.Mute(**data)
    Client.get_client(CLIENT_NAME).send_request('mute', data)


def default(button, device_type, device_id):
    '''
    Called when the default button is toggled
    '''

    if button.get_active() is False:
        return

    data = {
        'index': {
            'device_type': device_type,
            'device_id': device_id
        }
    }

    requests_schema.Default(**data)
    Client.get_client(CLIENT_NAME).send_request('default', data)


def volume(scale, device_type, device_id):
    '''
    Called when there's a value change in a volume scale
    '''

    data = {
        'index': {
            'device_type': device_type,
            'device_id': device_id
        },
        'volume': scale.get_value()
    }

    requests_schema.Volume(**data)
    Client.get_client(CLIENT_NAME).send_request('volume', data)


def list_devices(device_type) -> list:
    data = {'device_type': device_type}
    requests_schema.DeviceList(**data)
    res: ipc_schema.Response = Client.get_client(CLIENT_NAME).send_request('list_devices', data)
    return res.data
