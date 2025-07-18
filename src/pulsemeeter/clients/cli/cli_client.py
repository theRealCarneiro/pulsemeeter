import logging
import gettext
import argparse

from pulsemeeter.settings import VERSION

LOG = logging.getLogger('generic')
_ = gettext.gettext

DEVICE_TYPES = {
    'device': ('hi', 'vi', 'a', 'b'),
    'input': ('hi', 'vi'),
    'output': ('a', 'b')
}


def make_device_type_parser(allowed_types, label="device"):
    '''
    Sets allowed types and return the correct parser
    '''

    def parser(device_type):
        '''
        Checks if a device type is valid
        '''
        if device_type in allowed_types:
            return device_type

        raise argparse.ArgumentTypeError(f"Invalid {label} type: {device_type}")

    return parser


def parse_device_id(device_id):
    '''
    Checks if the device type is a number gt 0
    '''
    if device_id.isdigit() and int(device_id) > 0:
        return device_id

    raise argparse.ArgumentTypeError(_("Invalid device id: %s") % device_id)


def add_device_args(parser, device_class='device'):
    '''
    Inserts device type and id args into a parser
    '''

    device_parser = make_device_type_parser(DEVICE_TYPES[device_class], label=device_class)
    parser.add_argument(f"{device_class}_type", type=device_parser)
    parser.add_argument(f"{device_class}_id", type=parse_device_id)


def parse_bool(value):
    if value.lower() in ('yes', 'true', 't', '1', 'on'):
        return True
    elif value.lower() in ('no', 'false', 'f', '0', 'off'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_args():
    LOG.debug('Parsing args...')
    parser = argparse.ArgumentParser(description='Pulsemeeter')
    subparser = parser.add_subparsers(dest='command')

    subparser.add_parser('init', help='INIT')

    subparser.add_parser('cleanup', help='Removes all virtual devices and connections made by pulsemeeter')

    volume_parser = subparser.add_parser('volume', help='Set the volume')
    add_device_args(volume_parser)
    volume_parser.add_argument('value', type=int)

    mute_parser = subparser.add_parser('mute', help='Set the mute state')
    add_device_args(mute_parser)
    mute_parser.add_argument('value', type=parse_bool, nargs='?', default=None)

    primary_parser = subparser.add_parser('primary', help='Set the primary device')
    add_device_args(primary_parser)

    connect_parser = subparser.add_parser('connect', help='Set the connection state')
    add_device_args(connect_parser, 'input')
    add_device_args(connect_parser, 'output')
    connect_parser.add_argument('value', type=parse_bool, nargs='?', default=None)

    parser.add_argument('-v', '--version', action='version', version=VERSION)

    return parser.parse_args()
