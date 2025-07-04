import logging
from typing import Literal

# from pydantic import BaseModel
from pulsemeeter.scripts import pmctl
from pulsemeeter.scripts import pmctl_async
from pulsemeeter.schemas.typing import PaDeviceType
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.app_model import AppModel
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.connection_model import ConnectionModel

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

        # we have to create the virtual devices first
        for device_type in ('vi', 'b'):
            for device_id in self.__dict__[device_type]:
                self.init_device(device_type, device_id)

        # now we connect the input devices
        for device_type in ('vi', 'hi'):
            for device_id in self.__dict__[device_type]:
                self.reconnect(device_type, device_id)

    def init_device(self, device_type, device_id):
        '''
        Create Pulse device
        '''
        device = self.__dict__[device_type][device_id]
        if device_type in ('vi', 'b') and not device.external:
            pmctl.init(device.device_type, device.name, device.channels)

    def bulk_connect(self, device_type, device_id, state):
        '''
        Recreate the pipewire connections for a device
        '''
        device = self.__dict__[device_type][device_id]
        if device_type in ('hi', 'vi'):
            for output_type, connection_list in device.connections.items():
                for output_id in connection_list:
                    self.set_connection(device_type, device_id, output_type, output_id, state, soft=True)
            return

        for input_type in ('hi', 'vi'):
            for input_id in self.__dict__[input_type]:
                self.set_connection(input_type, input_id, device_type, device_id, state, soft=True)

    def reconnect(self, device_type, device_id):
        '''
        Recreate the pipewire connections for a device
        '''
        device = self.__dict__[device_type][device_id]

        if device_type in ('hi', 'vi'):
            for output_type, connection_list in device.connections.items():
                for output_id, connection in connection_list.items():
                    self.set_connection(device_type, device_id, output_type, output_id, connection.state, soft=True)
            return

        for input_type in ('hi', 'vi'):
            for input_id, input_device in self.__dict__[input_type].items():
                connection = input_device.connections[device_type][device_id]
                self.set_connection(input_type, input_id, device_type, device_id, connection.state, soft=True)

        # for output_type, connection_list in device.connections.items():
        #     for output_id, connection in connection_list.items():
        #         self.set_connection(input_type, input_id, output_type, output_id, connection.state)

    def update_device(self, device_schema, device_type, device_id):
        device = self.__dict__[device_type][device_id]

        # check if valid
        DeviceModel(**device_schema)

        self.bulk_connect(device_type, device_id, False)

        if device_type in ('vi', 'b'):
            pmctl.remove(device.name)

        # update values
        device.update_device_settings(device_schema)

        # change connection settings
        if device_type in ('vi', 'hi'):
            self.handle_input_change(device_type, device_id)
        else:
            self.handle_output_change(device_type, device_id)

        if device_type in ('vi', 'b'):
            self.init_device(device_type, device_id)

        self.reconnect(device_type, device_id)

    def cleanup(self):
        '''
        Removes all pulse devices from pulse
        '''
        for _, device_list in self.__dict__.items():
            for _, device in device_list.items():
                if device.device_class == 'virtual':
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

    def set_connection(self, input_type, input_id, output_type, output_id, state: bool = None, soft=False):
        input_device = self.__dict__[input_type][input_id]
        output_device = self.__dict__[output_type][output_id]
        connection_model = input_device.connections[output_type][output_id]

        # by soft we mean dont save to config
        if soft is False:
            input_device.set_connection(output_type, output_id, state, emit=False)

        input_sel_channels = input_device.get_selected_channel_list()
        output_sel_channels = output_device.get_selected_channel_list()
        port_map = connection_model.str_port_map(input_sel_channels, output_sel_channels)

        pmctl.connect(input_device.name, output_device.name, state, port_map=port_map)

        # print(input_sel_channels, output_sel_channels, port_map)

    def update_connection(self, input_type, input_id, output_type, output_id, connection_model):
        input_device = self.__dict__[input_type][input_id]
        cur_connection_model = input_device.connections[output_type][output_id]
        state = connection_model.state
        # print(cur_connection_model, connection_model)
        # print(input_type, input_id, output_type, output_id)

        self.set_connection(input_type, input_id, output_type, output_id, False)

        cur_connection_model.auto_ports = connection_model.auto_ports
        cur_connection_model.port_map = connection_model.port_map

        self.set_connection(input_type, input_id, output_type, output_id, state)

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

    def handle_output_change(self, output_type, output_id):
        '''
        Creates connections to the output in all inputs
        '''
        output_device = self.__dict__[output_type][output_id]
        for input_type in ('vi', 'hi'):
            for _, input_device in self.__dict__[input_type].items():
                connection_model = input_device.connections[output_type][output_id]
                connection_model.output_sel_channels = output_device.selected_channels
                connection_model.nick = output_device.nick

    def handle_input_change(self, input_type, input_id):
        '''
        Creates connections to existing output devices
        '''
        input_device = self.__dict__[input_type][input_id]
        for output_type in input_device.connections:
            for output_id in self.__dict__[output_type]:
                connection_model = input_device.connections[output_type][output_id]
                connection_model.input_sel_channels = input_device.selected_channels

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

        self.init_device(device_type, device_id)

        self.emit('device_new', device_type, device_id, device)

        return device_type, device_id, device

    def remove_device(self, device_type: str, device_index: str):
        '''
        Remove a device from config
        '''

        # if its a hardwre device, we have to disconnect them
        if device_type in ('a', 'hi'):
            self.bulk_connect(device_type, device_index, False)

        device = self.__dict__[device_type].pop(device_index)

        # remove connection dict from input devices
        if device.get_type() in ('a', 'b'):
            for input_type in ('vi', 'hi'):
                for _, input_device in self.__dict__[input_type].items():
                    input_device.connections[device_type].pop(device_index)

        if device.device_class == 'virtual':
            pmctl.remove(device.name)

        self.emit('device_remove', device_type, device_index)
        return device

    def list_pa_devices(self):
        pass

    @classmethod
    def list_devices(self, device_type):
        dvtp = 'sink' if device_type == 'a' else 'source'
        pa_device_list = pmctl.list_devices(dvtp)

        device_list = []
        for device in pa_device_list:
            device_model = DeviceModel.pa_to_device_model(device, dvtp)
            device_list.append(device_model)

        return device_list

    def list_device_names(self, pa_device_type: PaDeviceType, monitor=False):
        dvl = []
        device_type = 'vi' if pa_device_type == 'sink' else 'b'
        for _, device in self.__dict__[device_type].items():

            name = device.name
            if monitor is True:
                name += '.monitor'

            dvl.append(device.name)

        return dvl

    async def event_listen(self, callback_function):
        async for event in pmctl_async.pulse_listener():

            if event.facility in ('sink_input', 'source_output'):
                app_type = 'sink_input' if event.facility == 'sink_input' else 'source_output'

                if event.t == 'change':
                    app = await pmctl_async.get_app_by_id(event.facility, event.index)
                    if app is None:
                        continue

                    self.emit('app_change', app_type, event.index, app)

                elif event.t == 'new':
                    app = await pmctl_async.get_app_by_id(event.facility, event.index)
                    if app is None:
                        continue

                    app_model = AppModel.pa_to_app_model(app, app_type)
                    self.emit('app_new', app_type, event.index, app_model)

                elif event.t == ('remove'):
                    self.emit('app_remove', app_type, event.index)

            elif event.facility in ('sink', 'source'):
                if event.t == 'change':
                    pulsectl_device = await pmctl_async.get_device_by_id(event.facility, event.index)

                    device_type, device_id, pm_device = self.find_device(event.facility, pulsectl_device.name)

                    if pm_device is None:
                        continue

                    pm_device.update_from_pa(pulsectl_device)
                    self.emit('device_change', device_type, device_id, pm_device)
                    continue

            # primary changes
            elif event.facility == 'server':
                continue
