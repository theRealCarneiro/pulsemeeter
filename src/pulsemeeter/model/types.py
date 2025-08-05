import gettext

from enum import Enum
from dataclasses import dataclass

from pydantic import Field

_ = gettext.gettext


DEVICE_TYPE_PRETTY = {
    'hi': _('Hardware Inputs'),
    'vi': _('Virtual Inputs'),
    'a': _('Hardware Outputs'),
    'b': _('Virtual Outputs'),
    'sink_input': _('Application Outputs'),
    'source_output': _('Application Inputs')
}


class PulseEventType(Enum):
    CHANGE = 'change'
    NEW = 'new'
    REMOVE = 'remove'


class PulseEventFacility(Enum):
    SINK = 'sink'
    SOURCE = 'source'
    SINK_INPUT = 'sink_input'
    SOURCE_OUTPUT = 'source_output'


@dataclass
class PulseEvent:
    type: PulseEventType
    facility: PulseEventFacility
    index: int


class PulseAppType(Enum):
    SINK_INPUT = 'sink_input'
    SOURCE_OUTPUT = 'source_output'


class PulseDeviceClass(Enum):
    VIRTUAL = 'virtual'
    HARDWARE = 'hardware'


class PulseDeviceType(Enum):
    SINK = 'sink'
    SOURCE = 'source'


class DeviceType(Enum):
    VI = 'vi'
    HI = 'hi'
    A = 'a'
    B = 'b'


class HardwareDeviceType(Enum):
    HI = 'hi'
    A = 'a'


class VirtualDeviceType(Enum):
    VI = 'vi'
    B = 'b'


class InputDeviceType(Enum):
    VI = 'vi'
    HI = 'hi'


class OutputDeviceType(Enum):
    A = 'a'
    B = 'b'
