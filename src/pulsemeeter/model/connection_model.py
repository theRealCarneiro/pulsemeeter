import gettext

from pydantic import Field, BaseModel

_ = gettext.gettext


def port_position(port: str) -> str:
    '''
    Returns the speaker position a PipeWire port name carries
        "port" is a port name without its node, e.g. 'playback_FL' gives 'FL',
        'monitor_MONO' gives 'MONO' and 'playback_AUX0' gives 'AUX0'
    '''
    return port.rpartition('_')[2]


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
    unrouted_ports: list[str] = Field(default_factory=list, exclude=True)  # dropped by automatic mapping
    missing_links: int = Field(default=0, exclude=True)  # manual map links to channels that are gone
    failed_pairs: list[str] = Field(default_factory=list, exclude=True)  # pairs pw-link refused
    order_pairs: list[str] = Field(default_factory=list, exclude=True)  # paired by order, names differ

    def clear_warnings(self):
        '''
        Forget what the last link left out, before linking again or when unlinked
        '''
        self.unrouted_ports = []
        self.missing_links = 0
        self.failed_pairs = []
        self.order_pairs = []

    def error_text(self):
        '''
        Returns why the last link failed, or '' when it did not
        '''
        if not self.connect_failed:
            return ''

        if self.missing_links:
            return _('Every channel the manual map links is missing')

        return self.connect_error or _('Failed to create route')

    def warning_text(self):
        '''
        Returns what the last link left out, one line per kind of gap, or '' when nothing was
        '''
        lines = []
        if self.unrouted_ports:
            lines.append(_('%s not routed') % ', '.join(port_position(port) for port in self.unrouted_ports))

        if self.missing_links and not self.connect_failed:
            lines.append(_('Links to missing channels in the manual map: %d') % self.missing_links)

        if self.failed_pairs:
            lines.append(_('Failed to link: %s') % ', '.join(self.failed_pairs))

        return '\n'.join(lines)

    def order_text(self):
        '''
        Returns the pairs automatic mapping matched by order, or '' when it matched by name
        '''
        if not self.order_pairs:
            return ''

        return _('No matching channel names, matched channels by order: %s') % ', '.join(self.order_pairs)

    def str_port_map(self, input_channels, output_channels):
        '''
        Returns a string formated portmap for pmctl
            "input_channels" and "output_channels" are lists of (channel index,
            channel name) pairs, as returned by DeviceModel.get_selected_channels
        '''
        ports: str = ''

        # auto port mapping
        if self.auto_ports is True:
            for input_port, output_port in pair_match(input_channels, output_channels):
                ports += f'{input_port}:{output_port} '

            return ports[:-1]

        # manual port mapping
        live_outputs = {index for index, _ in output_channels}
        for position, target_ports in enumerate(self.port_map):

            # the map outlives the channel list when a device loses channels
            if position >= len(input_channels):
                continue

            input_port = input_channels[position][0]
            for target_port in target_ports:
                if target_port in live_outputs:
                    ports += f'{input_port}:{target_port} '

        return ports[:-1]

    def unrouted_channels(self, input_channels, output_channels, output_positions):
        '''
        Returns the indexes of the input channels automatic mapping leaves
        without a target, whose audio the route would drop
            "output_positions" are all the positions the output device has,
            selected or not

        A channel whose position the user deselected on the output device is
        left out on purpose, so it is not counted
        '''
        routed = {input_index for input_index, _ in pair_match(input_channels, output_channels)}
        deselected = set(output_positions) - {name for _, name in output_channels}
        return [
            index for index, name in input_channels
            if index not in routed and name not in deselected
        ]

    def count_missing_links(self, input_channels, output_channels):
        '''
        Returns how many links of the manual port map lead from or to a channel
        the devices do not have right now
        '''
        live_outputs = {index for index, _ in output_channels}
        return sum(
            position >= len(input_channels) or target not in live_outputs
            for position, targets in enumerate(self.port_map)
            for target in targets
        )

    def routing_grid(self, input_ports, output_ports, input_channels, output_channels):
        '''
        Build the routing grid from the port lists offered by PW.
        '''
        rows = [
            (position, input_ports[channel])
            for position, (channel, _name) in enumerate(input_channels)
            if channel < len(input_ports)
        ]
        cols = [
            (channel, output_ports[channel])
            for channel, _name in output_channels
            if channel < len(output_ports)
        ]

        live_outputs = {channel for channel, _ in cols}
        position_of = {channel: position for position, (channel, _name) in enumerate(input_channels)}
        checked = set()

        # auto port mapping
        if self.auto_ports is True:
            for input_channel, output_channel in pair_match(input_channels, output_channels):
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


def pair_match(input_channels, output_channels):
    '''
    Pair up input and output channels for automatic port mapping.
        "input_channels" and "output_channels" are lists of (channel index,
        channel name) pairs, as returned by DeviceModel.get_selected_channels

    Channels are paired by speaker position. A lone channel on either side
    pairs with every channel on the other, and sides that share no position
    pair in order, up to the shorter side.

    Returns a list of (input channel index, output channel index) pairs
    '''
    # A single input channel, mono or picked out of a device, plays on every output channel
    if len(input_channels) == 1:
        return [(input_channels[0][0], output_index) for output_index, _ in output_channels]

    # Likewise every input channel plays on a single output channel
    if len(output_channels) == 1:
        return [(input_index, output_channels[0][0]) for input_index, _ in input_channels]

    # Pair by order up to the shorter side, leftover inputs are reported as unrouted
    if matched_by_order(input_channels, output_channels):
        return [
            (input_index, output_index)
            for (input_index, _), (output_index, _) in zip(input_channels, output_channels)
        ]

    # Repeated names (UNK) pair one to one, taking each output channel once in order
    output_indexes = {}
    for index, name in output_channels:
        output_indexes.setdefault(name, []).append(index)

    # same speaker position on both sides
    pairs = []
    for index, name in input_channels:
        if output_indexes.get(name):
            pairs.append((index, output_indexes[name].pop(0)))

    return pairs


def removed_pairs(old_map, new_map):
    '''
    Returns the pairs of a pmctl port map string that a newer one no longer
    has, as a port map string
    '''
    kept = set(new_map.split())
    return ' '.join(pair for pair in old_map.split() if pair not in kept)


def matched_by_order(input_channels, output_channels):
    '''
    Whether automatic mapping pairs these channels by order rather than by name:
    neither side is a lone channel, and they share no speaker position
    '''
    input_names = {name for _, name in input_channels}
    output_names = {name for _, name in output_channels}
    return len(input_channels) > 1 and len(output_channels) > 1 and not input_names & output_names
