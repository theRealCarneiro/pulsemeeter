from meexer.scripts import pmctl
from meexer.schemas.device_schema import DeviceSchema, DeviceFlags, ConnectionSchema


# TODO: Plugins, Reconnect, Update Device, Update Connection, Change Device
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
        pass

    def update_connection(self, connection):
        '''
        Changes the settings of connection, e.g. latency and portmap
        '''
        # TODO: disconnect old connection
        # TODO: change settings
        # TODO: recreate connection
        pass

    def update_device(self, device: DeviceSchema):
        '''
        Edit device settings
        '''
        pass

    def change_device(self):
        '''
        Changes the hardware device being used
        '''
        # TODO: disconnect old device
        # TODO: change name/description to new device
        # TODO: recreate connections
        pass

    def connect(self, output_type: str, output_id: str, target: str, state: bool = None):
        '''
        Changes the state of a connection
            "output_type" is either 'vi', 'hi', 'a' or 'b'
            "output_id" is the id of the output device
            "target" is the name of the output device
            "state" is a bool that represents the state of the connection
                True mean connect, False means disconnect
        '''
        if state is None:
            state = not self.connections[output_type][output_id].state

        if output_type not in self.connections:
            self.connections[output_type] = {}

        if output_id not in self.connections[output_type]:
            self.connections[output_type][output_id] = ConnectionSchema()

        self.connections[output_type][output_id].state = state

        portmap = self.connections[output_type][output_id].port_map

        pmctl.connect(self.name, target, state, port_map=portmap)

    def destroy(self):
        '''
        Destroy device if virtual, if hardware destroy connections
        '''
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

    @staticmethod()
    def list_devices(device_type: str):
        pa_device_list = pmctl.list_devices(device_type)
        device_list = []

        for device in pa_device_list:
            device_model = DeviceModel(
                name=device.name,
                description=device.description,
                channels=device.channels,
                channel_list=device.channels_list,
                device_type=device_type,
                device_class='hardware',
                mute=bool(device.mute),
                volume=device.volume  # TODO: fix volume in model
            )
            device_list.append(device_model)

        return device_list
