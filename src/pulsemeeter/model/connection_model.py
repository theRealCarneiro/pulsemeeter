from itertools import product

from pydantic import Field, BaseModel
# from pulsemeeter.scripts import pmctl
from pulsemeeter.model.signal_model import SignalModel
# from pulsemeeter.model.device_model import DeviceModel


class ConnectionModel(BaseModel):
    nick: str  # output nick
    # output_type: str
    # output_id: str
    state: bool = False
    latency: int | None = None
    auto_ports: bool = True
    # input_name: str
    # output_name: str
    input_sel_channels: list[bool]
    output_sel_channels: list[bool]
    port_map: list[list[int]] = Field(default_factory=list)

    def str_port_map(self, input_sel_channels, output_sel_channels):
        '''
        Returns a string formated portmap for pmctl
            "output_type" is either 'a' or 'b'
            "output_id" is an int > 0
            "output" is the DeviceModel of the output device
        '''
        # output_ports = output.get_selected_channel_list()
        # input_ports: list = self.get_selected_channel_list()
        ports: str = ''

        # auto port mapping
        if self.auto_ports is True:

            # iterate until when the shorter ends
            for input_port, output_port in pair_match(input_sel_channels, output_sel_channels):
                ports += f'{input_port}:{output_port} '

            return ports[:-1]

        # manual port mapping
        port_map = self.port_map
        for input_port, target_ports in enumerate(port_map):
            for target_port in target_ports:
                ports += f'{input_sel_channels[input_port]}:{target_port} '

        ports = ports[:-1]

        return ports

    def reload_settings(self, input_sel_channels=None, output_sel_channels=None):
        '''
        Should be called on device change event to reset the port mapping if the
        channel map changed
        '''
        if input_sel_channels and self.input_sel_channels != input_sel_channels:
            self.input_sel_channels = input_sel_channels
            self.auto_ports = True
            self.port_map = []

        if output_sel_channels and self.output_sel_channels != output_sel_channels:
            self.output_sel_channels = output_sel_channels
            self.auto_ports = True
            self.port_map = []

    def set_connect(self, state):
        if state is None:
            state = not self.state

        # change state
        self.state = state
        # self.propagate('connection', state)
        # pmctl.connect(self.input_name, self.output_name, state, port_map=self.str_port_map())

    # def update_connection(self, output_type: str, output_id: str,
    #                       connection: ConnectionSchema):
    #     '''
    #     Changes the settings of connection, e.g. latency and portmap
    #     '''
        # target = connection.target
        # state = connection.state

        # disconnect
        # self.connect(output_type, output_id, target, False, change_config=False)

        # update connection
        # self.connections[output_type][output_id].__dict__.update(connection)

        # connect
        # self.connect(output_type, output_id, target, state, change_config=False)


def pair_match(list_a, list_b):

    if len(list_a) == len(list_b):
        return list(zip(list_a, list_b))

    # if len(list_a) < len(list_b):
    #     return list(product(list_b, list_a))

    return list(product(list_a, list_b))
