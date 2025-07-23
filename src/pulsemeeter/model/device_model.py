import re
import logging
from typing import Literal
from pulsemeeter.schemas.typing import Volume, PaDeviceType, DeviceClass
from pydantic import BaseModel, root_validator, validator
# from pulsemeeter.schemas.device_schema import ConnectionModel
from pulsemeeter.scripts import pmctl
from pulsemeeter.schemas import pulse_mappings
from pulsemeeter.model.connection_model import ConnectionModel
# from pulsemeeter.model.connection_manager_model import ConnectionManagerModel
from pulsemeeter.model.signal_model import SignalModel

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
    # plugins: list[PluginSchema] = []

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
        # if not re.match('^[a-zA-Z0-9._-]+$', name):
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

        # print(correct_channel_list)
        return correct_channel_list

    # @root_validator(pre=True)
    # def set_connections(cls, values):
    #     '''
    #     '''
    #     if (values['device_type'] == 'sink' and values['device_class'] == 'virtual' or
    #             values['device_type'] == 'source' and values['device_class'] == 'hardware'):
    #
    #         if 'connections' not in values or values['connections'] is None:
    #             values['connections'] = {}
    #             for device_type in ('a', 'b'):
    #                 values['connections'][device_type] = {}
    #
    #     return values

    device_type: Literal['sink', 'source']
    device_class: Literal['virtual', 'hardware']

    def get_correct_name(self):
        '''
        Get the device name that will be used, e.g. when using plugins you need
        the name of the effect sink
        '''
        # TODO: actually implement this, but not really necessary until plugins
        return self.name

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
        # device.connections = self.connections
        self.__dict__.update(device)
        self.name = device['name']
        self.description = device['description']
        self.nick = device['nick']
        self.channels = device['channels']
        self.external = device['external']
        self.channel_list = device['channel_list']
        self.selected_channels = device['selected_channels']
        # self.volume = device.volume
        # self.device_type = device.device_type
        # self.device_class = device.device_class
        return 0

    # def change_device(self):
    #     '''
    #     Changes the hardware device being used (perhaps not needed bc update_device_settings)
    #     '''
    #     raise NotImplementedError

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
        # pmctl.mute(self.device_type, self.name, state)
        # if emit is True:
        #     self.propagate('mute', self.mute)

    def set_volume(self, val: int, emit: bool = True):
        '''
        Change device volume
            "val" is the new volume level
        '''

        # convert to list if only int
        if isinstance(val, int):
            val = [val] * self.channels

        # change volume only for selected channels
        # if self.selected_channels is not None:
        #     selected = self.selected_channels
        #     val = [val[i] if selected[i] else self.volume[i] for i in range(self.channels)]

        if self.volume == val:
            return

        self.volume = val

        # pmctl.set_volume(self.device_type, self.name, val[0])
        # if emit is True:
        #     self.propagate('volume', self.volume[0])

    def set_primary(self, state: bool = True, emit: bool = True):
        '''
        Set device as default
        '''
        self.primary = state
        device_type = self.get_type()
        # pmctl.set_primary(device_type, self.name)
        # if emit is True:
        #     self.emit('primary', device_type, self.name)

    def create_connection(self, device_type, device_id, connection_model):
        # the new device can only be a or b, and this device can only be hi or vi
        if self.get_type() in ('a', 'b') or device_type in ('hi', 'vi'):
            return

        # connection_model.connect('connection', self.set_connection, device_type, device_id)
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

        # if emit is True:
        #     self.emit('connection', output_type, output_id, state)

        # pmctl.connect(self.input_name, self.output_name, state, port_map=self.str_port_map())

        return connection_model

    # def get_volume(self):
    #     return self.volume[0]

    # maybe use that instead of List[bool] for selected_channels ?
    def get_selected_channel_list(self) -> list[int]:
        '''
        Returns a list with the index of the selected channels
        '''

        sel_channels = self.selected_channels

        if sel_channels is None:
            return list(range(self.channels))

        return [i for i in range(len(sel_channels)) if sel_channels[i] is True]

    def make_port_map(self, output_type: str, output_id: str, output) -> str:
        '''
        Returns a string formated portmap for pmctl
            "output_type" is either 'a' or 'b'
            "output_id" is an int > 0
            "output" is the DeviceModel of the output device
        '''
        output_ports = output.get_selected_channel_list()
        input_ports: list = self.get_selected_channel_list()
        ports: str = ''

        # auto port mapping
        if self.connections[output_type][output_id].auto_ports is True:

            # iterate until when the shorter ends
            for input_port, output_port in zip(input_ports, output_ports):
                ports += f'{input_port}:{output_port} '

        # manual port mapping
        else:
            port_map = self.connections[output_type][output_id].port_map
            for input_port, target_ports in enumerate(port_map):
                for target_port in target_ports:
                    ports += f'{input_ports[input_port]}:{target_port} '

        ports = ports[:-1]

        return ports

    def str_port_map(self, output_type: str, output_id: str, output) -> str:
        '''
        Returns a string formated portmap for pmctl
            "output_type" is either 'a' or 'b'
            "output_id" is an int > 0
            "output" is the DeviceModel of the output device
        '''
        output_ports = output.get_selected_channel_list()
        input_ports: list = self.get_selected_channel_list()
        ports: str = ''

        # auto port mapping
        if self.connections[output_type][output_id].auto_ports is True:

            # iterate until when the shorter ends
            for input_port, output_port in zip(input_ports, output_ports):
                ports += f'{input_port}:{output_port} '

        # manual port mapping
        else:
            port_map = self.connections[output_type][output_id].port_map
            for input_port, target_ports in enumerate(port_map):
                for target_port in target_ports:
                    ports += f'{input_ports[input_port]}:{target_port} '

        ports = ports[:-1]

        return ports

    # def check_volume_changes(self, volume: list[int]):
    #
    #     # pm volume lists don't have all the channels from the org device, so we need
    #     # to check the selected_channels list to know what channel does that volume represent
    #     vol_index = 0
    #     for channel_index, selected_channel in enumerate(self.selected_channels):
    #         print(volume, self.volume)
    #
    #         # if channel is not selected, we just ignore it
    #         if selected_channel is False:
    #             continue
    #
    #         # check if volume has changed
    #         if self.volume[vol_index] != volume[channel_index]:
    #             self.set_volume(volume[channel_index])
    #             # print('Volume changed: ', self.volume[vol_index], volume[channel_index])
    #             # return True, volume[channel_index]
    #             return True
    #
    #         vol_index += 1
    #
    #     return False

    # def check_mute_changes(self, mute: bool):
    #     return self.mute != mute

    # def check_for_changes(self, volume: list[int], mute: bool):
    #     self.check_volume_changes(volume)
    #     self.check_mute_changes(mute)

    # @classmethod
    def update_from_pa(self, pa_device):
        '''
        Convert a pulsectl device into an Device Model
            "pa_device" is either a PulseSinkInfo or a PulseSourceInfo
            "device" is a device model
            "device_type" is either 'sink' or 'source'
        '''

        vol = []
        for index, channel in enumerate(self.selected_channels):
            if channel is True:
                vol.append(round(pa_device.volume.values[index] * 100))

        if vol == self.volume and bool(pa_device.mute) == self.mute:
            return False

        self.set_mute(bool(pa_device.mute), emit=True)
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
