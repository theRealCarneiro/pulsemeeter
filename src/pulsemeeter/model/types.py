import gettext

from enum import Enum
from dataclasses import dataclass

_ = gettext.gettext


DEVICE_TYPE_PRETTY = {
    'hi': _('Hardware Inputs'),
    'vi': _('Virtual Inputs'),
    'a': _('Hardware Outputs'),
    'b': _('Virtual Outputs'),
    'sink_input': _('Application Outputs'),
    'source_output': _('Application Inputs')
}


DEVICE_TYPE_DESCRIPTION = {
    'hi': _('Physical sources such as microphones and line-in.'),
    'vi': _('Virtual sinks that applications can play into.'),
    'a': _('Physical sinks such as speakers and headphones.'),
    'b': _('Virtual sources that applications can capture from.'),
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
