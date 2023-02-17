from meexer.scripts import pmctl
from meexer.schemas.device_schema import DeviceSchema, DeviceFlags, ConnectionSchema


# TODO: Plugins, Change Device
class DeviceModel(DeviceSchema):
    '''
    Child class of DeviceSchema, implements pmctl calls to PA and PW
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.create()
        self.reconnect(True)

    def get_type(self):
        if self.device_type == 'sink':
            if self.device_class == 'virtual':
                return 'vi'
            else:
                return 'a'
        else:
            if self.device_class == 'virtual':
                return 'b'
            else:
                return 'hi'

    def create(self):
        '''
        Create device if virtual
        '''
        if self.device_class == 'virtual' and not self.flags & DeviceFlags.EXTERNAL:
            ret = pmctl.init(self.device_type, self.name)
            if ret == 126:
                raise

    def reconnect(self, state: bool):
        '''
        Changes the state of active connections, does not affect config
            "state" represents what state should the connections be changed into,
                True will recreate active connections, False will destroy them
        '''

        for device_type, connections in self.connections.keys():
            for device_id, conn in connections.keys():
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
        self.connect(output_type, output_id, target, False, change_config=False)
        self.connections[output_type][output_id].__dict__.update(connection)
        self.connect(output_type, output_id, target, state, change_config=False)

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
        pass

    def connect(self, output_type: str, output_id: str, target: str,
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
            self.connections[output_type][output_id] = ConnectionSchema()

        if change_config is True:
            self.connections[output_type][output_id].state = state

        portmap = self.connections[output_type][output_id].port_map

        pmctl.connect(self.name, target, state, port_map=portmap)

    def destroy(self):
        '''
        Destroy device if virtual, if hardware destroy connections
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
        pmctl.mute('sink', self.name, state)

    def set_default(self):
        '''
        Set device as default
        '''
        self.primary = True
        if self.device_class == 'virtual':
            pmctl.set_primary('sink', self.name)

    def set_volume(self, val: int):
        '''
        Change device volume
            "val" is the new volume level
        '''
        pmctl.volume(self.device_type, self.name, val)

    @staticmethod
    def list_devices(device_type: str):
        pa_device_list = pmctl.list_devices(device_type)
        device_list = []

        for device in pa_device_list:
            device_model = DeviceModel(
                name=device.name,
                description=device.description,
                channels=len(device.volume.values),
                channel_list=device.channel_list,
                device_type=device_type,
                device_class='hardware',
                mute=bool(device.mute),
                volume=[i * 100 for i in device.volume.values]  # TODO: fix volume in model
            )
            device_list.append(device_model)

        return device_list
