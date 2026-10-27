import re
import logging
from typing import Literal
from pulsemeeter.schemas.typing import Volume, PaDeviceType, DeviceClass
from pydantic import BaseModel, Field, root_validator, validator
from pulsemeeter.scripts import pmctl
from pulsemeeter.schemas import pulse_mappings
from pulsemeeter.model.connection_model import ConnectionModel, port_position

LOG = logging.getLogger("generic")


class DeviceModel(BaseModel):
    '''
    Child class of DeviceModel, implements pmctl calls
    '''
    name: str
    nick: str
    description: str
    device_type: PaDeviceType
    device_class: DeviceClass
    volume: list[Volume] = None
    mute: bool = False
    flags: int = 0
    external: bool = False
    primary: bool | None
    channels: int
    channel_list: list[str]
    connections: dict[str, dict[str, ConnectionModel]] = {'a': {}, 'b': {}}
    selected_channels: list[bool] | None

    # Transient runtime status (not persisted).
    # init_failed/init_error: hard error (e.g. pw-cli failed to create) - UI shows warning.
    # present: whether the underlying PA device currently exists. If False
    # without an init_failed, the UI just dims the device name as "disconnected".
    init_failed: bool = Field(default=False, exclude=True)
    init_error: str = Field(default='', exclude=True)
    present: bool = Field(default=True, exclude=True)

    @root_validator(pre=True)
    def set_nick_description(cls, values):
        '''
        A validator that sets the nick and description of a device if none are
        provided
        '''

        if 'nick' not in values:
            values['nick'] = values.get('name')

        if 'description' not in values:
            values['description'] = values.get('nick')

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
        if re.compile(r'^\s|\s$').search(name):
            raise ValueError('Invalid name')

        return name

    @validator('channel_list', always=True)
    def check_channel_list(cls, channel_list):
        '''
        A validator that converts pulseaudio style channel names to pipewire
        '''
        correct_channel_list = []
        for channel in channel_list:
            alias = pulse_mappings.CHANNEL_NAME_ALIASES.get(channel)
            if alias is not None:
                channel = alias

            correct_channel_list.append(channel)

        return correct_channel_list

    device_type: Literal['sink', 'source']
    device_class: Literal['virtual', 'hardware']

    def get_type(self):
        if self.device_type == 'sink':
            if self.device_class == 'virtual':
                return 'vi'
            return 'a'

        if self.device_class == 'virtual':
            return 'b'
        return 'hi'

    def update_device_settings(self, device):
        '''
        Update device settings
        '''
        self.__dict__.update(device)
        self.name = device['name']
        self.description = device['description']
        self.nick = device['nick']
        self.channels = device['channels']
        self.external = device['external']
        self.channel_list = device['channel_list']
        self.selected_channels = device['selected_channels']
        return 0

    def set_mute(self, state: bool, emit: bool = True):
        '''
        Mute device
            "state": bool, True mean mute, False means unmute
        '''
        if self.mute == state:
            return

        if state is None:
            state = not self.mute

        self.mute = state

    def set_volume(self, val: int, emit: bool = True):
        '''
        Change device volume
            "val" is the new volume level
        '''

        # convert to list if only int
        if isinstance(val, int):
            val = [val] * self.channels

        if self.volume == val:
            return

        self.volume = val

    def set_primary(self, state: bool = True, emit: bool = True):
        '''
        Set device as default
        '''
        self.primary = state

    def create_connection(self, device_type, device_id, connection_model):
        # the new device can only be a or b, and this device can only be hi or vi
        if self.get_type() in ('a', 'b') or device_type in ('hi', 'vi'):
            return

        self.connections[device_type][device_id] = connection_model

    def set_connection(self, output_type: str, output_id: str, state: bool = None, emit: bool = True):
        '''
        Changes the state of a connection, or create it if it does not exist
            "output_type" is either 'vi', 'hi', 'a' or 'b'
            "output_id" is the id of the output device
            "target" is the name of the output device
            "state" is a bool that represents the state of the connection
                True mean connect, False means disconnect
            "change_config" means save the state change of the connection,
                useful for e.g. removing connections on cleanup
        '''

        connection_model = self.connections[output_type][output_id]

        # pmctl is here on connection model (or should i put it here? hmm)
        connection_model.set_connect(state)

        return connection_model

    # maybe use that instead of List[bool] for selected_channels ?
    def get_selected_channel_list(self) -> list[int]:
        '''
        Returns a list with the index of the selected channels
        '''

        sel_channels = self.selected_channels

        if sel_channels is None:
            return list(range(self.channels))

        return [i for i in range(len(sel_channels)) if sel_channels[i] is True]

    def get_selected_channels(self, ports: list[str]) -> list[tuple[int, str]]:
        '''
        Returns the selected channels as (index, channel name) pairs, the form
        the automatic port mapping pairs devices up on
            "ports" are the device's live port names, as returned by pmctl.get_ports

        Names are read off the ports rather than channel_list
        '''

        sel_channels = self.selected_channels or []

        return [
            (i, port_position(port))
            for i, port in enumerate(ports)

            # a channel the config has never seen cannot have been deselected
            if i >= len(sel_channels) or sel_channels[i] is True
        ]

    def update_from_pa(self, pa_device):
        '''
        Convert a pulsectl device into an Device Model
            "pa_device" is either a PulseSinkInfo or a PulseSourceInfo
            "device" is a device model
            "device_type" is either 'sink' or 'source'
        '''

        vol = []
        pa_values = pa_device.volume.values
        for index, channel in enumerate(self.selected_channels or []):
            if channel is True and index < len(pa_values):
                vol.append(round(pa_values[index] * 100))

        mute = bool(pa_device.mute)
        if vol == self.volume and mute == self.mute:
            return False

        self.set_mute(mute, emit=True)
        if vol:
            self.set_volume(vol[0], emit=True)
        return True

    @classmethod
    def pa_to_device_model(cls, device, device_type: str):
        '''
        Convert a pulsectl device into an Device Model
            "device" is either a PulseSinkInfo or a PulseSourceInfo
            "device_type" is either 'sink' or 'source'
        '''

        device_class = 'hardware' if pmctl.is_hardware_device(device) else 'virtual'

        device_model = cls(
            name=device.name,
            description=device.description,
            channels=len(device.volume.values),
            channel_list=device.channel_list,
            selected_channels=[True for _ in range(len(device.volume.values))],
            device_type=device_type,
            device_class=device_class,
            mute=bool(device.mute),
            volume=[round(i * 100) for i in device.volume.values]
        )

        return device_model

    @classmethod
    def list_devices(cls, pa_device_list: list, device_type: str):
        '''
        Convert a list of pulsectl devices into a list of Device Models
            "device_type" is either 'sink' or 'source'
        '''
        device_list = []

        for device in pa_device_list:
            device_model = cls.pa_to_device_model(device, device_type)
            device_list.append(device_model)

        return device_list
