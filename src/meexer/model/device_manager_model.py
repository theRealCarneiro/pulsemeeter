import logging
from typing import Callable

from pydantic import BaseModel
from meexer.scripts import pmctl
from meexer.model.device_model import DeviceModel
from meexer.model.signal_model import SignalModel
from meexer.model.connection_model import ConnectionModel

LOG = logging.getLogger("generic")


class DeviceManagerModel(SignalModel):
    '''
    Model for the config file, has functions to load and write the file
    '''

    vi: dict[str, DeviceModel] = {}
    b: dict[str, DeviceModel] = {}
    hi: dict[str, DeviceModel] = {}
    a: dict[str, DeviceModel] = {}

    def model_post_init(self, _):

        # we have to create the devices first
        for device_type, device_list in self.__dict__.items():
            for device_id in device_list:
                self.init_device(device_type, device_id)

        # we dont want to connect to a device that hasnt been created yet
        for device_type, device_list in self.__dict__.items():
            for device_id in device_list:
                self.reconnect(device_type, device_id)

    def init_device(self, device_type, device_id):
        '''
        Create Pulse device
        '''
        device = self.__dict__[device_type][device_id]
        if device_type in ('vi', 'b'):
            pmctl.init(device.device_type, device.name, device.channels)

    def reconnect(self, input_type, input_id):
        '''
        Recreate the pipewire connections for a device
        '''
        device = self.__dict__[input_type][input_id]
        for output_type, connection_list in device.connections.items():
            for output_id, connection in connection_list.items():
                self.set_connection(input_type, input_id, output_type, output_id, connection.state)

    def cleanup(self):
        '''
        Removes all pulse devices from pulse
        '''
        for _, device_list in self.__dict__.items():
            for _, device in device_list.items():
                pmctl.remove(device.name)

    def set_volume(self, device_type, device_id, volume: int):
        device = self.__dict__[device_type][device_id]
        device.set_volume(volume, emit=False)
        pmctl.set_volume(device.device_type, device.name, volume)

    def set_mute(self, device_type, device_id, state: bool):
        device = self.__dict__[device_type][device_id]
        device.set_mute(state, emit=False)
        pmctl.mute(device.device_type, device.name, state)

    def set_primary(self, device_type, device_id):
        device = self.__dict__[device_type][device_id]
        if device.primary is True:
            return

        for other_device_id, other_device in self.__dict__[device_type].items():
            if device_id != other_device_id:
                other_device.set_primary(False, emit=False)

        device.set_primary(True, emit=False)
        pmctl.set_primary(device.device_type, device.name)

    def set_connection(self, input_type, input_id, output_type, output_id, state: bool = None):
        input_device = self.__dict__[input_type][input_id]
        output_device = self.__dict__[output_type][output_id]
        connection_model = input_device.connections[output_type][output_id]

        input_device.set_connection(output_type, output_id, state, emit=False)

        input_sel_channels = input_device.get_selected_channel_list()
        output_sel_channels = output_device.get_selected_channel_list()
        port_map = connection_model.str_port_map(input_sel_channels, output_sel_channels)

        pmctl.connect(input_device.name, output_device.name, state, port_map=port_map)

        # print(input_sel_channels, output_sel_channels, port_map)

    def get_device(self, device_type: str, device_id: str):
        '''
        Get a device by it's id
        '''
        return self.__dict__[device_type][device_id]

    def find_device(self, device_class, name):
        for device_type in ('a', 'vi') if device_class == 'sink' else ('b', 'hi'):
            for device_id, device in self.__dict__[device_type].items():
                if device.name == name:
                    return device_type, device_id, device

        return None, None, None

    def get_primary(self, device_type: str):
        '''
        Get the primary device from device_type
        '''
        for _, device in self.vi.items() if device_type == 'sink' else self.b.items():
            if device.primary is True:
                return device.name

        return None

    def create_connection(self, input_device, output_device):
        return ConnectionModel(
            nick=output_device.nick,
            input_name=input_device.name,
            output_name=output_device.name,
            input_sel_channels=input_device.selected_channels,
            output_sel_channels=output_device.selected_channels
        )

    def handle_new_output(self, output_type, output_id, output_device):
        '''
        Creates connections to the output in all inputs
        '''
        for input_type in ('vi', 'hi'):
            for _, input_device in self.__dict__[input_type].items():
                connection_model = self.create_connection(input_device, output_device)
                input_device.create_connection(output_type, output_id, connection_model)

    def handle_new_input(self, input_device: DeviceModel):
        '''
        Creates connections to existing output devices
        '''
        for output_type in input_device.connections:
            for output_id, output_device in self.__dict__[output_type].items():
                connection_model = self.create_connection(input_device, output_device)
                input_device.create_connection(output_type, output_id, connection_model)

    def create_device(self, device_dict: dict):
        '''
        Insert a device into config
        '''

        device = DeviceModel(**device_dict)
        device_type = device.get_type()
        device_dict = self.__dict__[device_type]

        # get max id
        device_id = max(device_dict, key=int, default='0')
        device_id = str(int(device_id) + 1)

        # Create connection models
        if device_type in ('vi', 'hi'):
            self.handle_new_input(device)
        else:
            self.handle_new_output(device_type, device_id, device)

        # add device to dict
        device_dict[device_id] = device

        # pmctl.init(device_type, device.name, device.channels)
        self.emit('device_new', device_type, device_id, device)

        return device_type, device_id, device

    def remove_device(self, device_type: str, device_index: str):
        '''
        Remove a device from config
        '''
        device = self.__dict__[device_type].pop(device_index)
        pmctl.remove(device.name)
        self.emit('device_remove', device_type, device_index)
        return device

    def list_pa_devices(self):
        pass

    def list_devices(self, device_type):
        dvtp = 'sink' if device_type == 'a' else 'source'
        pa_device_list = pmctl.list_devices(dvtp)

        device_list = []
        for device in pa_device_list:
            device_model = DeviceModel.pa_to_device_model(device, dvtp)
            device_list.append(device_model)

        return device_list
