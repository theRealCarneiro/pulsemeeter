from typing import Literal
from pydantic import conint, constr, Field

Volume = conint(ge=0, le=153)
ValidName = Field(pattern=r'^[a-zA-Z0-9_.-]+$')
DeviceID = Field(pattern=r'^[1-9]\d*$')  # any number greater than 0

AppType = Literal['sink_input', 'source_output']
DeviceClass = Literal['virtual', 'hardware']
PaDeviceType = Literal['sink', 'source']
DeviceType = Literal['a', 'b', 'vi', 'hi']
VirtualDeviceType = Literal['b', 'vi']
HardwareDeviceType = Literal['a', 'hi']
InputDeviceType = Literal['vi', 'hi']
OutputDeviceType = Literal['a', 'b']


# DeviceTypeList = ('a', 'b', 'vi', 'hi')
# VirtualDeviceList = ('b', 'vi')
# HardwareDeviceList = ('a', 'hi')
# InputDeviceList = ('vi', 'hi')
# OutputDeviceList = ('a', 'b')
