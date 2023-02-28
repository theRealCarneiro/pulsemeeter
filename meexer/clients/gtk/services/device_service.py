from meexer.ipc.client import Client
# from meexer.schemas.ipc_schema import SubscriptionFlags

from meexer.schemas import requests_schema

CLIENT_NAME = 'gtk'


'''
This module is for implementing the gtk signal callback for devices and making the requests
to the server
'''


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
