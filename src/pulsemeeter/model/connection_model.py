from itertools import product

from pydantic import Field, BaseModel


class ConnectionModel(BaseModel):
    nick: str  # output nick
    state: bool = False
    latency: int | None = None
    auto_ports: bool = True
    input_sel_channels: list[bool]
    output_sel_channels: list[bool]
    port_map: list[list[int]] = Field(default_factory=list)
    route_volume: int = 100  # 0-153, per-route volume (only used when use_loopback=True)
    use_loopback: bool = False  # opt-in for per-route volume via pw-loopback

    # Transient runtime status, prevent saving to config
    connect_failed: bool = Field(default=False, exclude=True)
    connect_error: str = Field(default='', exclude=True)

    def str_port_map(self, input_sel_channels, output_sel_channels):
        '''
        Returns a string formated portmap for pmctl
            "output_type" is either 'a' or 'b'
            "output_id" is an int > 0
            "output" is the DeviceModel of the output device
        '''
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

    def routing_grid(self, input_ports, output_ports, input_sel_channels, output_sel_channels):
        '''
        Build the routing grid from the port lists offered by PW.
        '''
        rows = [
            (position, input_ports[channel])
            for position, channel in enumerate(input_sel_channels)
            if channel < len(input_ports)
        ]
        cols = [
            (channel, output_ports[channel])
            for channel in output_sel_channels
            if channel < len(output_ports)
        ]

        live_outputs = {channel for channel, _ in cols}
        position_of = {channel: position for position, channel in enumerate(input_sel_channels)}
        checked = set()

        # auto port mapping
        if self.auto_ports is True:
            for input_channel, output_channel in pair_match(input_sel_channels, output_sel_channels):
                if input_channel < len(input_ports) and output_channel in live_outputs:
                    checked.add((position_of[input_channel], output_channel))

            return rows, cols, checked

        # manual port mapping
        live_positions = {position for position, _ in rows}
        for position, targets in enumerate(self.port_map):
            if position not in live_positions:
                continue
            for output_channel in targets:
                if output_channel in live_outputs:
                    checked.add((position, output_channel))

        return rows, cols, checked

    def merge_port_map(self, active_pairs, rendered_positions, map_rows):
        '''
        Merge edited grid pairs back into a port_map.
        '''
        port_map = [list(targets) for targets in self.port_map][:map_rows]
        while len(port_map) < map_rows:
            port_map.append([])

        for position in rendered_positions:
            if position < len(port_map):
                port_map[position] = []

        for position, output_channel in active_pairs:
            if position < len(port_map):
                port_map[position].append(output_channel)

        for targets in port_map:
            targets.sort()

        return port_map

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


def pair_match(list_a, list_b):

    if len(list_a) == len(list_b):
        return list(zip(list_a, list_b))

    return list(product(list_a, list_b))
