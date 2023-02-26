import re
from typing import Literal
from pydantic import BaseModel, Field, root_validator, validator


class DeviceFlags:
    NOFLAGS = 0
    EXTERNAL = 1 << 0


class ConnectionSchema(BaseModel):
    target: str
    nick: str
    state: bool = False
    latency: int | None
    auto_ports: bool = False
    port_map: list[list[int]] = []


class PluginSchema(BaseModel):
    name: str
    label: str
    plugin: str
    control: list[float]


# class VolumeSchema(BaseModel):
    # value: int = Field(100, ge=0, le=153, description='volume must be ge 0 le 153')


class DeviceSchema(BaseModel):
    name: str
    nick: str
    description: str
    device_type: Literal['sink', 'source']
    device_class: Literal['virtual', 'hardware']
    volume: list[int] = None
    mute: bool = False
    flags: int = 0
    primary: bool | None
    channels: int
    channel_list: list[str]
    connections: dict[str, dict[str, ConnectionSchema]] = {}
    selected_channels: list[bool] | None
    plugins: list[PluginSchema] = []

    @root_validator(pre=True)
    def set_nick_description(cls, values):
        '''
        A validator that sets the nick and description of a device if none are
        provided
        '''
        name = values.get('name')

        if 'nick' not in values:
            values['nick'] = name
        if 'description' not in values:
            values['description'] = name

        return values

    @root_validator(pre=True)
    def check_volume(cls, values):
        '''
        Set volume list if None are set
        '''
        if 'volume' not in values:
            values['volume'] = [100 for _ in range(values['channels'])]

        if isinstance(values['volume'], int):
            values['volume'] = [values['volume'] for _ in range(len(values['channels']))]

        return values

    @root_validator(pre=True)
    def no_hardware_primary(cls, values):
        '''
        Sets hardware devices primary as None
        '''
        if values['device_class'] == 'hardware':
            values['primary'] = None

        elif 'primary' not in values:
            values['primary'] = False

        return values

    @validator('name', always=True)
    def check_name(cls, name):
        '''
        A validator that checks if the name is valid
        '''
        if re.match('^[a-zA-Z-_.]+ ?([a-zA-z+-_.]+)?$', name):
            return name
