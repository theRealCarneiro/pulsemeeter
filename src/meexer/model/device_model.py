from meexer.schemas.device_schema import DeviceSchema, ConnectionSchema


# TODO: Plugins, Change Device
class DeviceModel(DeviceSchema):
    '''
    Child class of DeviceSchema, implements pmctl calls
    '''

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

    def update_device_settings(self, device: DeviceSchema):
        '''
        Update device settings
        '''
        device.connections = self.connections
        self.__dict__.update(device)
        return 0

    def change_device(self):
        '''
        Changes the hardware device being used (perhaps not needed bc update_device_settings)
        '''
        # TODO: disconnect old device
        # TODO: change name/description to new device
        # TODO: recreate connections
        raise NotImplementedError

    def connect(self, output_type: str, output_id: str, state: bool, nick: str):
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
            self.connections[output_type][output_id] = ConnectionSchema(nick=nick)

        # change state
        print(self.connections)
        self.connections[output_type][output_id].state = state

    def update_connection(self, output_type: str, output_id: str,
                          connection: ConnectionSchema):
        '''
        Changes the settings of connection, e.g. latency and portmap
        '''
        # target = connection.target
        # state = connection.state

        # disconnect
        # self.connect(output_type, output_id, target, False, change_config=False)

        # update connection
        self.connections[output_type][output_id].__dict__.update(connection)

        # connect
        # self.connect(output_type, output_id, target, state, change_config=False)

    def set_mute(self, state: bool):
        '''
        Mute device
            "state": bool, True mean mute, False means unmute
        '''
        self.mute = state

    def set_default(self):
        '''
        Set device as default
        '''
        self.primary = True

    def set_volume(self, val: int):
        '''
        Change device volume
            "val" is the new volume level
        '''

        # convert to list if only int
        if isinstance(val, int):
            val = [val for _ in self.volume]

        # change volume only for selected channels
        if self.selected_channels is not None:
            selected = self.selected_channels
            val = [val[i] if selected[i] is True else self.volume[i] for i in range(self.channels)]

        self.volume = val

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

    @classmethod
    def update_from_pa(cls, pa_device, device_model, device_type: str):
        '''
        Convert a pulsectl device into an Device Model
            "pa_device" is either a PulseSinkInfo or a PulseSourceInfo
            "device" is a device model
            "device_type" is either 'sink' or 'source'
        '''

        device_model.channel_list = pa_device.channel_list
        device_model.device_type = device_type
        device_model.mute = bool(pa_device.mute)
        device_model.volume = [i * 100 for i in pa_device.volume.values]

        return device_model

    @classmethod
    def pa_to_device_model(cls, device, device_type: str):
        '''
        Convert a pulsectl device into an Device Model
            "device" is either a PulseSinkInfo or a PulseSourceInfo
            "device_type" is either 'sink' or 'source'
        '''
        pa_sink_hardware = 0x0004
        print()
        print(device.name, device.flags, device.flags & pa_sink_hardware)
        print()
        device_class = 'hardware' if device.flags & pa_sink_hardware else 'virtual'
        device_model = cls(
            name=device.name,
            description=device.description,
            channels=len(device.volume.values),
            channel_list=device.channel_list,
            selected_channels=[True for _ in range(len(device.volume.values))],
            device_type=device_type,
            device_class=device_class,
            mute=bool(device.mute),
            volume=[int(i * 100) for i in device.volume.values]
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
