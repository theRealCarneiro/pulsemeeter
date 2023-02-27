from meexer.scripts import pmctl
from meexer.schemas.device_schema import DeviceSchema, DeviceFlags, ConnectionSchema


# TODO: Plugins, Change Device
class DeviceModel(DeviceSchema):
    '''
    Child class of DeviceSchema, implements pmctl calls
    '''

    # def __init__(self, *args, **kwargs):
        # super().__init__(*args, **kwargs)

        # self.create()
        # self.reconnect(True)

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

    def create(self):
        '''
        Create device if virtual
        '''
        if self.device_class == 'virtual' and not self.flags & DeviceFlags.EXTERNAL:
            pmctl.init(self.device_type, self.name)
            # if ret == 126:
                # raise

    def update_device_settings(self, device: DeviceSchema):
        '''
        Update device settings
        '''
        self.destroy()
        device.connections = self.connections
        self.__dict__.update(device)
        self.create()
        self.reconnect(True)
        return 0

    def change_device(self):
        '''
        Changes the hardware device being used (perhaps not needed bc update_device_settings)
        '''
        # TODO: disconnect old device
        # TODO: change name/description to new device
        # TODO: recreate connections
        raise NotImplementedError

    def connect(self, output_type: str, output_id: str, output: DeviceSchema,
                state: bool = None, change_config: bool = False):
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

        # toggle the state of the connection
        if state is None:
            state = not self.connections[output_type][output_id].state

        # check if output_type key is in the connections dict
        if output_type not in self.connections:
            self.connections[output_type] = {}

        # create connection if it doesn't exist
        if output_id not in self.connections[output_type]:
            conn_schema = ConnectionSchema(target=output.name, nick=output.nick)
            self.connections[output_type][output_id] = conn_schema

        if change_config is True:
            self.connections[output_type][output_id].state = state

        str_port_map = self.str_port_map(output_type, output_id, output)

        pmctl.connect(self.get_correct_name(), output.get_correct_name(),
                      state, port_map=str_port_map)

    def reconnect(self, state: bool):
        '''
        Changes the state of active connections, does not affect config
            "state" represents what state should the connections be changed into,
                True will recreate active connections, False will destroy them
        '''

        for device_type, connections in self.connections.items():
            for device_id, conn in connections.items():
                if conn.state is True:
                    self.connect(device_type, device_id, conn.target, state,
                                 change_config=False)

        return 0

    def update_connection(self, output_type: str, output_id: str,
                          connection: ConnectionSchema):
        '''
        Changes the settings of connection, e.g. latency and portmap
        '''
        # TODO: disconnect old connection
        # TODO: change settings
        # TODO: recreate connection

        target = connection.target
        state = connection.state

        # disconnect
        self.connect(output_type, output_id, target, False, change_config=False)

        # update connection
        self.connections[output_type][output_id].__dict__.update(connection)

        # connect
        self.connect(output_type, output_id, target, state, change_config=False)

    def destroy(self):
        '''
        Destroy connections, estroy device if virtual
        '''
        # TODO: remove plugins
        self.reconnect(False)
        if self.device_class == 'virtual' and not self.flags & DeviceFlags.EXTERNAL:
            pmctl.remove(self.name)

    def set_mute(self, state: bool):
        '''
        Mute device
            "state": bool, True mean mute, False means unmute
        '''
        self.mute = state
        pmctl.mute(self.device_type, self.name, state)

    def set_default(self):
        '''
        Set device as default
        '''
        self.primary = True
        if self.device_class == 'virtual':
            pmctl.set_primary(self.device_type, self.name)

    def set_volume(self, val: int):
        '''
        Change device volume
            "val" is the new volume level
        '''
        pmctl.volume(self.device_type, self.name, val)

    # TODO: maybe use that instead of List[bool] for selected_channels ?
    def get_selected_channel_list(self) -> list[int]:
        '''
        Returns a list with the index of the selected channels
        '''

        sel_channels = self.selected_channels

        if sel_channels is None:
            return list(range(self.channels))

        return [i for i in range(len(sel_channels)) if sel_channels[i] is True]

    def str_port_map(self, output_type: str, output_id: str, output: DeviceSchema):
        '''
        Returns a string formated portmap for pmctl
            "output_type" is either 'a' or 'b'
            "output_id" is an int > 0
            "output" is the DeviceSchema of the output device
        '''
        output_ports = output.get_selected_channel_list()
        input_ports: list = self.get_selected_channel_list()
        ports: str = ''

        # auto port mapping
        if self.connections[output_type][output_id].auto_ports is True:

            # get the number of channels of the device with less channels
            num_connection_channel = min(len(input_ports), len(output_ports))

            for port in range(num_connection_channel):
                ports += f'{input_ports[port]}:{output_ports[port]} '

        # manual port mapping
        else:
            port_map = self.connections[output_type][output_id].port_map
            for input_port in range(len(port_map)):
                for output_port in port_map[input_port]:
                    ports += f'{input_ports[input_port]}:{output_port} '

        ports = ports[:-1]

        return ports

    @classmethod
    def pa_to_device_model(cls, device, device_type: str):
        '''
        Convert a pulsectl device into an Device Model
            "device" is either a PulseSinkInfo or a PulseSourceInfo
            "device_type" is either 'sink' or 'source'
        '''

        device_model = cls(
            name=device.name,
            description=device.description,
            channels=len(device.volume.values),
            channel_list=device.channel_list,
            selected_channels=[True for _ in range(len(device.volume.values))],
            device_type=device_type,
            device_class='hardware',
            mute=bool(device.mute),

            # TODO: fix volume in model
            volume=[i * 100 for i in device.volume.values]
        )

        return device_model

    @classmethod
    def list_devices(cls, device_type: str):
        '''
        Convert a list of pulsectl devices into a list of Device Models
            "device_type" is either 'sink' or 'source'
        '''
        pa_device_list = pmctl.list_devices(device_type)
        device_list = []

        for device in pa_device_list:
            device_model = cls.pa_to_device_model(device, device_type)
            device_list.append(device_model)

        return device_list
