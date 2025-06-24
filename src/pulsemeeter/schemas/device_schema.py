import re
from typing import Literal
from pydantic import BaseModel, root_validator, validator, Field


class DeviceFlags:
    NOFLAGS = 0
    EXTERNAL = 1 << 0


class ConnectionSchema(BaseModel):
    nick: str
    state: bool = False
    latency: int | None = None
    auto_ports: bool = True
    port_map: list[str] = Field(default_factory=list)


class PluginSchema(BaseModel):
    name: str
    label: str
    plugin: str
    control: list[float]


CHANNEL_MAPS = {
    "mono": ["mono"],
    "stereo": ["front-left", "front-right"],
    "quad": ["front-left", "front-right", "rear-left", "rear-right"],
    "5.0": ["front-left", "front-right", "front-center", "rear-left", "rear-right"],
    "5.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right"],
    "7.1": ["front-left", "front-right", "front-center", "lfe", "rear-left", "rear-right", "side-left", "side-right"]
}

INVERSE_CHANNEL_MAPS = {1: "1", 2: "2", 4: "3", 5: "4", 6: "5", 8: "6"}


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
        if not re.match('^[a-zA-Z-_.]+ ?([a-zA-z+-_.]+)?$', name):
            raise ValueError('Invalid name')

        return name

    @root_validator(pre=True)
    def set_connections(cls, values):
        '''
        '''
        if (values['device_type'] == 'sink' and values['device_class'] == 'virtual' or
                values['device_type'] == 'source' and values['device_class'] == 'hardware'):

            if 'connections' not in values or values['connections'] is None:
                values['connections'] = {}
                for device_type in ('a', 'b'):
                    values['connections'][device_type] = {}

        return values

    device_type: Literal['sink', 'source']
    device_class: Literal['virtual', 'hardware']
