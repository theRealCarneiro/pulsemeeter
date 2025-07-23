import sys
import logging

from pydantic import PrivateAttr
from pulsemeeter.scripts import pmctl
from pulsemeeter.schemas.typing import PaDeviceType
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.repository.device_repository import DeviceRepository

LOG = logging.getLogger("generic")


class DeviceController(SignalModel):
    '''
    DeviceController manages device operations and emits signals for UI and other components.

    Signals:
        device_new(device_type: str, device_id: str, device: DeviceModel):
            Emitted when a new device is created.
        device_remove(device_type: str, device_id: str):
            Emitted when a device is removed.
        device_change(device_type: str, device_id: str, device: DeviceModel):
            Emitted when a device's configuration changes.
        connect(input_type: str, input_id: str, output_type: str, output_id: str, state: bool):
            Emitted when a connection between devices is changed.

    Attributes:
        device_repository (DeviceRepository): The repository managing device data.
    '''

    device_repository: DeviceRepository

    def __init__(self, device_repository: DeviceRepository, noinit=False):
        '''
        Initialize the device manager model, check for pmctl, create and connect devices, and cache them.
        '''
        super().__init__()

        self.device_repository = device_repository
        if not pmctl.is_pipewire():
            LOG.error('ERROR: pipewire-pulse not detected, pipewire-pulse is required')
            sys.exit(1)

        # we have to create the virtual devices first
        for device_type in ('vi', 'b'):
            for device_id in self.device_repository.get_devices_by_type(device_type):
                self.init_device(device_type, device_id, cache=False)

        # now we connect the input devices
        for device_type in ('vi', 'hi'):
            for device_id in self.device_repository.get_devices_by_type(device_type):
                self.reconnect(device_type, device_id)

    def init_device(self, device_type, device_id, cache=True):
        '''
        Create Pulse device.
        Args:
            device_type (str): Type of device ('vi', 'b', etc.).
            device_id (str): Device identifier.
            cache (bool): Whether to cache the device.
        '''
        device = self.device_repository.get_device(device_type, device_id)
        if device_type in ('vi', 'b') and not device.external and not pmctl.device_exists(device.name):
            pmctl.create_device(device.device_type, device.name, device.channels, device.channel_list)

        # if cache:
        #     self.append_device_cache(device_type, device_id, device)

    def bulk_connect(self, device_type, device_id, state):
        '''
        Recreate the pmctl connections for a device.
        Args:
            device_type (str): Type of device.
            device_id (str): Device identifier.
            state (bool): Connection state.
        '''
        device = self.device_repository.get_device(device_type, device_id)
        if device_type in ('hi', 'vi'):
            for output_type, connection_list in device.connections.items():
                for output_id in connection_list:
                    self.set_connection(device_type, device_id, output_type, output_id, state, soft=True)
            return

        for input_type in ('hi', 'vi'):
            for input_id in self.device_repository.get_devices_by_type(input_type):
                self.set_connection(input_type, input_id, device_type, device_id, state, soft=True)

    def reconnect(self, device_type: str, device_id: str):
        '''
        Recreate the pmctl connections for a device.
        Args:
            device_type (str): Type of device.
            device_id (str): Device identifier.
        '''
        device = self.device_repository.get_device(device_type, device_id)

        if device_type in ('hi', 'vi'):
            for output_type, connection_list in device.connections.items():
                for output_id, connection in connection_list.items():
                    if not connection.state:
                        continue

                    self.set_connection(device_type, device_id, output_type, output_id, connection.state, soft=True)
            return

        for input_type in ('hi', 'vi'):
            input_dict = self.device_repository.get_devices_by_type(input_type)
            for input_id, input_device in input_dict.items():
                connection = input_device.connections[device_type][device_id]
                self.set_connection(input_type, input_id, device_type, device_id, connection.state, soft=True)

    def update_device(self, device_schema, device_type, device_id):
        '''
        Update a device's configuration and connections.
        Args:
            device_schema (dict): New device configuration.
            device_type (str): Type of device.
            device_id (str): Device identifier.
        '''
        device = self.device_repository.get_device(device_type, device_id)

        self.bulk_connect(device_type, device_id, False)

        if device_type in ('vi', 'b') and device.external is False:
            pmctl.remove_device(device.name)

        # update values
        self.device_repository.update_device(device_type, device_id, device_schema)

        # change connection settings
        if device_type in ('vi', 'hi'):
            self.handle_input_change(device_type, device_id)
        else:
            self.handle_output_change(device_type, device_id)

        if device_type in ('vi', 'b'):
            self.init_device(device_type, device_id)
            if device.primary:
                pmctl.set_primary(device.device_type, device.name)

        self.reconnect(device_type, device_id)

        self.emit('device_change', device_type, device_id, device)

    def cleanup(self):
        '''
        Removes all pulse devices from pulse.
        '''
        device_dict = self.device_repository.get_all_devices()
        for _, device_list in device_dict.items():
            for _, device in device_list.items():
                if device.device_class == 'virtual' and not device.external:
                    pmctl.remove_device(device.name)

    def set_volume(self, device_type, device_id, volume: int):
        '''
        Set the volume of a device.
        Args:
            device_type (str): Type of device.
            device_id (str): Device identifier.
            volume (int): Volume value.
        '''
        device = self.device_repository.get_device(device_type, device_id)
        device.set_volume(volume, emit=False)
        pmctl.set_volume(device.device_type, device.name, volume)

    def set_mute(self, device_type, device_id, state: bool):
        '''
        Set the mute state of a device.
        Args:
            device_type (str): Type of device.
            device_id (str): Device identifier.
            state (bool): Mute state.
        '''
        device = self.device_repository.get_device(device_type, device_id)
        if state is None:
            state = not device.mute

        device.set_mute(state, emit=False)
        pmctl.mute(device.device_type, device.name, state)

    def set_primary(self, device_type, device_id):
        '''
        Set a device as primary.
        Args:
            device_type (str): Type of device.
            device_id (str): Device identifier.
        '''
        device = self.device_repository.get_device(device_type, device_id)
        if device.primary is True:
            return

        self.unset_primary(device_type)

        device.set_primary(True, emit=False)
        pmctl.set_primary(device.device_type, device.name)

    def unset_primary(self, device_type):
        '''
        Unset all devices as primary for a given type.
        Args:
            device_type (str): Type of device.
        '''
        for _, device in self.device_repository.get_devices_by_type(device_type).items():
            device.set_primary(False, emit=False)

    def set_connection(self, input_type, input_id, output_type, output_id, state: bool = None, soft=False):
        '''
        Set the connection state between two devices.
        Args:
            input_type (str): Input device type.
            input_id (str): Input device identifier.
            output_type (str): Output device type.
            output_id (str): Output device identifier.
            state (bool, optional): Connection state. If None, toggles state.
            soft (bool): If True, do not save to config.
        '''
        input_device = self.device_repository.get_device(input_type, input_id)
        output_device = self.device_repository.get_device(output_type, output_id)
        connection_model = input_device.connections[output_type][output_id]

        if state is None:
            state = not connection_model.state

        # by soft we mean dont save to config
        if soft is False:
            input_device.set_connection(output_type, output_id, state, emit=False)
            self.emit('connect', input_type, input_id, output_type, output_id, state)

        input_sel_channels = input_device.get_selected_channel_list()
        output_sel_channels = output_device.get_selected_channel_list()
        port_map = connection_model.str_port_map(input_sel_channels, output_sel_channels)

        pmctl.link_channels(input_device.name, output_device.name, port_map, state)

    def update_connection(self, input_type, input_id, output_type, output_id, connection_model):
        '''
        Update the connection model between two devices.
        Args:
            input_type (str): Input device type.
            input_id (str): Input device identifier.
            output_type (str): Output device type.
            output_id (str): Output device identifier.
            connection_model: New connection model.
        '''
        input_device = self.device_repository.get_device(input_type, input_id)
        cur_connection_model = input_device.connections[output_type][output_id]
        state = connection_model.state

        self.set_connection(input_type, input_id, output_type, output_id, False)

        cur_connection_model.auto_ports = connection_model.auto_ports
        cur_connection_model.port_map = connection_model.port_map

        self.set_connection(input_type, input_id, output_type, output_id, state)

    # def get_primary(self, device_type: str):
    #     '''
    #     Get the primary device from device_type.
    #     Args:
    #         device_type (str): Type of device ('sink' or 'source').
    #     Returns:
    #         DeviceModel or None.
    #     '''
    #     for _, device in self.vi.items() if device_type == 'sink' else self.b.items():
    #         if device.primary is True:
    #             return device
    #
    #     return None

    def create_connection(self, input_device, output_device):
        '''
        Create a connection model between two devices.
        Args:
            input_device (DeviceModel): Input device.
            output_device (DeviceModel): Output device.
        Returns:
            ConnectionModel: The connection model object.
        '''
        return ConnectionModel(
            nick=output_device.nick,
            input_name=input_device.name,
            output_name=output_device.name,
            input_sel_channels=input_device.selected_channels,
            output_sel_channels=output_device.selected_channels
        )

    def handle_output_change(self, output_type, output_id):
        '''
        Reconfigure connections to the output in all inputs.
        Args:
            output_type (str): Output device type.
            output_id (str): Output device identifier.
        '''
        output_device = self.device_repository.get_device(output_type, output_id)
        for input_type in ('vi', 'hi'):
            for _, input_device in self.device_repository.get_devices_by_type(input_type).items():
                connection_model = input_device.connections[output_type][output_id]
                connection_model.nick = output_device.nick
                connection_model.reload_settings(output_sel_channels=output_device.selected_channels)

    def handle_input_change(self, input_type, input_id):
        '''
        Reconfigure connections on a specific input device.
        Args:
            input_type (str): Input device type.
            input_id (str): Input device identifier.
        '''
        input_device = self.device_repository.get_device(input_type, input_id)
        for output_type in input_device.connections:
            for output_id in self.device_repository.get_devices_by_type(output_type):
                connection_model = input_device.connections[output_type][output_id]
                connection_model.reload_settings(input_sel_channels=input_device.selected_channels)

    def handle_new_output(self, output_type, output_id, output_device):
        '''
        Create connections to the output in all inputs.
        Args:
            output_type (str): Output device type.
            output_id (str): Output device identifier.
            output_device (DeviceModel): Output device object.
        '''
        for input_type in ('vi', 'hi'):
            for _, input_device in self.device_repository.get_devices_by_type(input_type).items():
                connection_model = self.create_connection(input_device, output_device)
                input_device.create_connection(output_type, output_id, connection_model)

    def handle_new_input(self, input_device: DeviceModel):
        '''
        Create connections to existing output devices for a new input device.
        Args:
            input_device (DeviceModel): The new input device.
        '''
        for output_type in input_device.connections:
            for output_id, output_device in self.device_repository.get_devices_by_type(output_type).items():
                connection_model = self.create_connection(input_device, output_device)
                input_device.create_connection(output_type, output_id, connection_model)

    def create_device(self, device_dict: dict):
        '''
        Insert a device into config.
        Args:
            device_dict (dict): Device configuration dictionary.
        Returns:
            Tuple of (device_type, device_id, device).
        '''
        device_type, device_id, device = self.device_repository.create_device(device_dict)
        if device_type in ('vi', 'hi'):
            self.handle_new_input(device)
        else:
            self.handle_new_output(device_type, device_id, device)

        self.init_device(device_type, device_id)
        self.emit('device_new', device_type, device_id, device)
        return device_type, device_id, device

    def remove_device(self, device_type: str, device_id: str, cache=True):
        '''
        Remove a device from config.
        Args:
            device_type (str): Type of device.
            device_index (str): Device identifier.
            cache (bool): Whether to update the cache.
        Returns:
            DeviceModel: The removed device object.
        '''
        if device_type in ('a', 'hi'):
            self.bulk_connect(device_type, device_id, False)

        device = self.device_repository.remove_device(device_type, device_id)

        # remove connection dict from input devices
        if device.get_type() in ('a', 'b'):
            for input_type in ('vi', 'hi'):
                for input_device in self.device_repository.get_devices_by_type(input_type).values():
                    input_device.connections[device_type].pop(device_id)

        # remove device from cache
        # if cache:
        #     self.pop_device_cache(device_type, device_id, device)

        if device.device_class == 'virtual':
            pmctl.remove_device(device.name)

        self.emit('device_remove', device_type, device_id)
        return device

    @classmethod
    def list_devices(self, device_type):
        '''
        List devices of a given type.
        Args:
            device_type (str): Type of device ('a' for sink, 'b' for source).
        Returns:
            list: List of DeviceModel objects.
        '''
        dvtp = 'sink' if device_type == 'a' else 'source'
        pa_device_list = pmctl.list_devices(dvtp)
        device_list = []
        for device in pa_device_list:
            device_model = DeviceModel.pa_to_device_model(device, dvtp)
            device_list.append(device_model)
        return device_list

    def list_device_names(self, pa_device_type: PaDeviceType, monitor=False):
        '''
        List device names for a given PulseAudio device type.
        Args:
            pa_device_type (PaDeviceType): 'sink' or 'source'.
            monitor (bool): Whether to append '.monitor' to names.
        Returns:
            list: List of device names.
        '''
        dvl = []
        device_type = 'vi' if pa_device_type == 'sink' else 'b'
        for _, device in self.device_repository.get_devices_by_type(device_type).items():

            name = device.name
            if monitor is True:
                name += '.monitor'

            dvl.append(device.name)

        return dvl

    def list_device_nicks(self, pa_device_type: PaDeviceType, monitor=False):
        '''
        List device nicknames for a given PulseAudio device type.
        Args:
            pa_device_type (PaDeviceType): 'sink' or 'source'.
            monitor (bool): Whether to append '.monitor' to nicks.
        Returns:
            list: List of (nick, name) tuples.
        '''
        dvl = []
        device_type = 'vi' if pa_device_type == 'sink' else 'b'
        for _, device in self.device_repository.get_devices_by_type(device_type).items():

            nick = device.nick
            if monitor is True:
                nick += '.monitor'

            dvl.append((nick, device.name))

        return dvl
