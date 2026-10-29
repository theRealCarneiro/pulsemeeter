import os
import re
import json
import time
import shutil
import signal
import logging
import pulsectl
import subprocess

from pulsectl import PulseSinkInfo, PulseSourceInfo, PulseSinkInputInfo, PulseSourceOutputInfo

LOG = logging.getLogger('generic')
PULSE = pulsectl.Pulse('pmctl')


def create_device(device_type: str, name: str, channels: int, position: list[str]) -> bool:
    '''
    Create a PipeWire device.
    Args:
        device_type (str): 'sink' or 'source'.
        name (str): Name of the device.
        channels (int): Number of audio channels.
        position (list[str]): Channel map positions.
    Returns:
        bool: True on success, raises on failure.
    '''

    class_map = {'sink': 'Sink', 'source': 'Source/Virtual'}
    media_class = f'Audio/{class_map[device_type]}'

    data = f'''{{
        factory.name=support.null-audio-sink
        node.name="{name}"
        node.description="{name}"
        media.class={media_class}
        audio.channels={channels}
        audio.position="{' '.join(position)}"
        monitor.channel-volumes=true
        object.linger=true
    }}'''
    command = ['pw-cli', 'create-node', 'adapter', data]
    ret, stdout, stderr = run_command(command, split=False)
    # pw-cli exits 0 even on protocol/syntax failures; detect those via stderr
    if ret != 0 or 'error' in (stderr or '').lower():
        # Only fail when the node was not created
        if not get_node_serial(name):
            raise RuntimeError(f"Failed to create device: {(stderr or stdout).strip() or 'pw-cli reported failure'}")
        LOG.debug('pw-cli reported errors but created %s: %s', name, stderr.strip())
    return True


def remove_device(name: str) -> bool:
    '''
    Remove a PipeWire device by name.
    Args:
        name (str): Name of the device to remove.
    Returns:
        bool: True on success, raises on failure.
    '''
    command = ['pw-cli', 'destroy', name]
    ret, stdout, stderr = run_command(command)
    if ret != 0:
        raise RuntimeError(f"Failed to remove device: {stderr}")
    return True


def link(input_name: str, output_name: str, state: bool = True) -> bool:
    '''
    Link or unlink two PipeWire devices (all channels).
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
        state (bool): True to link, False to unlink.
    Returns:
        bool: True when the link ends up in the requested state.
    '''
    operation = [] if state else ['-d']
    command = ['pw-link', input_name, output_name, *operation]
    # The C locale keeps pw-link's error text in English, so it can be matched below
    ret, _, stderr = run_command(command, env={**os.environ, 'LC_ALL': 'C'})

    # pw-link fails when the link is already in the requested state, as on every reconnect
    already = 'File exists' if state else 'No such file or directory'
    return ret == 0 or already in stderr


def link_channels(input_name: str, output_name: str, channel_map: str, state: bool = True, *,
                  input_ports: list[str] | None = None, output_ports: list[str] | None = None) -> list[str]:
    '''
    Link or unlink two PipeWire devices using a channel map string (e.g. '0:0 1:1').
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
        channel_map (str): Channel map string, e.g. '0:0 1:1'.
        state (bool): True to link, False to unlink.
        input_ports (list[str]): Output ports of the input device, when the
            caller already read them to build channel_map. Read here if None.
        output_ports (list[str]): Input ports of the output device, likewise.
    Returns:
        list[str]: The pairs that could not be linked, as 'input_port -> output_port'.
            Raises when linking and no pair could be linked at all.
    '''
    if input_ports is None:
        input_ports = get_ports('output', input_name)
    if output_ports is None:
        output_ports = get_ports('input', output_name)

    # Check ports before the empty map, since missing ports also produce an empty map
    if not input_ports or not output_ports:
        if not state:
            return []
        raise RuntimeError(f'Ports not found for devices {input_name} {output_name}')

    if not channel_map:
        return []

    linked = 0
    unlinked = []
    for pair in channel_map.split(' '):
        input_id, output_id = pair.split(':')
        input_index, output_index = int(input_id), int(output_id)

        # Drop pairs that no longer have a port instead of failing every channel of the route.
        if not 0 <= input_index < len(input_ports) or not 0 <= output_index < len(output_ports):
            LOG.warning(
                'Skipping out of range channel pair %s for %s (%d ports) -> %s (%d ports)',
                pair, input_name, len(input_ports), output_name, len(output_ports)
            )
            unlinked.append(pair)
            continue

        input_port = f'{input_name}:{input_ports[input_index]}'
        output_port = f'{output_name}:{output_ports[output_index]}'
        if not link(input_port, output_port, state=state):
            LOG.warning('pw-link failed for %s -> %s', input_port, output_port)
            unlinked.append(f'{input_ports[input_index]} -> {output_ports[output_index]}')
            continue

        linked += 1

    if linked == 0 and state:
        raise RuntimeError(
            f'No channel of {channel_map} could be linked for devices {input_name} {output_name}'
        )

    return unlinked


def make_loopback_name(input_name: str, output_name: str) -> str:
    '''
    Generate a deterministic loopback name for a connection.
    Sanitizes to alphanumeric, underscores, hyphens, and dots only.
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
    Returns:
        str: Sanitized loopback name.
    '''
    raw = f'pm_route_{input_name}_to_{output_name}'
    return re.sub(r'[^a-zA-Z0-9._-]', '_', raw)


def loopback_nodes(loopback_name: str) -> tuple[str, str]:
    '''
    Get the node names pw-loopback gives its two streams.
    Args:
        loopback_name (str): The loopback name used when creating.
    Returns:
        tuple: (capture stream, playback stream).
    '''
    return f'input.{loopback_name}', f'output.{loopback_name}'


def get_node_serial(node_name: str) -> str:
    '''
    Get the PipeWire object.serial for a node via pw-cli, bypassing PulseAudio.
    Args:
        node_name (str): The PipeWire node.name.
    Returns:
        str: The object.serial, or empty string if not found.
    '''
    ret, stdout, _ = run_command(['pw-cli', 'info', node_name], split=False)
    if ret != 0 or not stdout:
        return ''
    match = re.search(r'object\.serial\s*=\s*"(\d+)"', stdout)
    return match.group(1) if match else ''


_NO_TARGET = ('', -1, '-1', None)


def has_target(props: dict) -> bool:
    '''
    True if a stream's own properties name a device: the app asked for one
    itself (e.g. pw-record --target). pipewire-pulse passes node props through
    to the pulse proplist, so no PipeWire lookup is needed.
    '''
    return any(props.get(k) not in _NO_TARGET for k in ('target.object', 'target.node', 'node.target'))


def is_movable(props: dict) -> bool:
    '''
    False if a stream refuses to be moved: node.dont-move (native clients),
    or node.dont-reconnect (what pipewire-pulse makes of PA_STREAM_DONT_MOVE).
    '''
    return not any(str(props.get(k)).lower() in ('true', '1') for k in ('node.dont-move', 'node.dont-reconnect'))


def get_app_pins() -> dict | None:
    '''
    Return {stream object id: pinned} for the streams the "default" metadata
    store has a target for: True if pinned to a device, False if set to follow
    the default (-1). Streams without an entry are left out; their own
    has_target() decides. Returns None if pw-dump is unavailable.
    '''
    try:
        # only the "default" metadata store, not the whole graph (~1 KB instead of ~1 MB)
        graph = json.loads(subprocess.check_output(['pw-dump', 'default'], stderr=subprocess.DEVNULL))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None

    pins = {}
    for obj in graph:
        if obj.get('type') == 'PipeWire:Interface:Metadata' and obj.get('props', {}).get('metadata.name') == 'default':
            for entry in obj.get('metadata', []):
                value = entry.get('value')
                if entry.get('key') not in ('target.object', 'target.node') or value in ('', None):
                    continue
                subject = entry.get('subject')
                pins[subject] = pins.get(subject, False) or str(value) != '-1'
    return pins


def _set_app_target(object_id: int, node_id, serial) -> bool:
    '''
    Write a stream's target to the "default" metadata the way pipewire-pulse
    does for a move: target.node is the device's node id, target.object its
    serial, -1 for both means "follow the default".
    '''
    try:
        for key, value in (('target.node', node_id), ('target.object', serial)):
            subprocess.run(['pw-metadata', '--', str(object_id), key, str(value), 'Spa:Id'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except OSError:
        return False


def pin_app(object_id: int, device_type: str, device_name: str) -> bool:
    '''
    Pin a stream (by PipeWire object id) to a device; WirePlumber moves it
    there. Unlike a pulse move, this also pins to the default device, which
    pipewire-pulse would turn into "follow the default".
    '''
    device = get_device_by_name(device_type, device_name)
    if device is None:
        return False
    node_id = device.proplist.get('object.id')
    serial = device.proplist.get('object.serial', device.index)
    if node_id is None:
        return False
    return _set_app_target(object_id, node_id, serial)


def unpin_app(object_id: int) -> bool:
    '''
    Set a stream (by PipeWire object id) to follow the default device. -1
    rather than clearing the target, so it also overrides a device the app
    asked for itself.
    '''
    return _set_app_target(object_id, -1, -1)


def create_loopback(name: str, capture_target: str, playback_target: str, channels: int) -> subprocess.Popen:
    '''
    Spawn a pw-loopback subprocess for per-route volume control.
    The session manager leaves its streams unlinked, the caller links their ports with pw-link.
    Args:
        name (str): Unique loopback name.
        capture_target (str): node.name the caller links to the capture stream.
        playback_target (str): node.name the caller links the playback stream to.
        channels (int): Number of audio channels.
    Returns:
        subprocess.Popen: The loopback subprocess handle.
    '''
    # Only the caller links the streams, the targets are recorded to match a running loopback to its route
    common = 'node.autoconnect=false node.linger=true node.virtual=true'

    # Channels are linked by index, so they carry no speaker position
    positions = ' '.join(f'AUX{index}' for index in range(channels))

    command = [
        'pw-loopback',
        '--name', name,
        '--channels', str(channels),
        '-m', f'[ {positions} ]',
        # node.virtual=true makes pipewire-pulse report no client for the streams,
        # which hides them from volume applets like plasma-pa
        '--capture-props', f'pulsemeeter.target={json.dumps(capture_target, ensure_ascii=False)} {common}',
        '--playback-props', f'pulsemeeter.target={json.dumps(playback_target, ensure_ascii=False)} {common}',
    ]

    LOG.debug('Creating loopback: %s', command)
    proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def destroy_loopback(proc: subprocess.Popen):
    '''
    Terminate a pw-loopback subprocess.
    Args:
        proc (subprocess.Popen): The loopback process to terminate.
    '''
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    LOG.debug('Loopback destroyed (pid=%s)', proc.pid if proc else None)


def _loopback_streams(loopback_name: str) -> tuple[list[PulseSinkInputInfo], list[PulseSourceOutputInfo]]:
    '''
    Find the streams of running pw-loopbacks with exactly this name.
    Args:
        loopback_name (str): The loopback name used when creating.
    Returns:
        tuple: (sink-inputs (playback side), source-outputs (capture side)).
    '''
    capture_name, playback_name = loopback_nodes(loopback_name)
    playback = [si for si in PULSE.sink_input_list() if si.proplist.get('node.name') == playback_name]
    capture = [so for so in PULSE.source_output_list() if so.proplist.get('node.name') == capture_name]
    return playback, capture


def set_route_volume(loopback_name: str, volume: int) -> bool:
    '''
    Set the volume of a pw-loopback sink-input by its loopback name.
    Args:
        loopback_name (str): The loopback name used when creating.
        volume (int): Volume value (0-153).
    Returns:
        bool: True on success, False if sink-input not found.
    '''
    volume = min(max(0, volume), 153)
    try:
        for si in _loopback_streams(loopback_name)[0]:
            channels = len(si.volume.values)
            vol = pulsectl.PulseVolumeInfo(volume / 100, channels)
            PULSE.volume_set(si, vol)
            return True
    except pulsectl.PulseError:
        LOG.error('Failed to set route volume for %s', loopback_name)
    return False


def wait_for_loopback(proc: subprocess.Popen, loopback_name: str, channels: int,
                      timeout: float = 2.0, interval: float = 0.01) -> bool:
    '''
    Poll until a pw-loopback is listed in PulseAudio and both its streams have a port per channel.
    Args:
        proc (subprocess.Popen): The loopback process, waiting stops if it exits.
        loopback_name (str): The loopback name to wait for.
        channels (int): The number of channels it was created with.
        timeout (float): Maximum time to wait in seconds.
        interval (float): Polling interval in seconds.
    Returns:
        bool: True if ready, False if it exited or timed out.
    '''
    capture_name, playback_name = loopback_nodes(loopback_name)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and proc.poll() is None:
        try:
            ports_ready = (len(get_ports('input', capture_name)) >= channels
                           and len(get_ports('output', playback_name)) >= channels)
            if ports_ready and _loopback_streams(loopback_name)[0]:
                return True
        except (pulsectl.PulseError, RuntimeError):
            pass
        time.sleep(interval)
    return False


def remove_bridge(loopback_name: str):
    '''
    Remove the sink older versions played a loopback into when routing to a virtual output.
    It outlives its loopback, and versions before 2.2 listed it as a regular sink.
    Args:
        loopback_name (str): The loopback name used when creating.
    '''
    bridge_name = f'{loopback_name}_bridge'
    if not get_node_serial(bridge_name):
        return

    try:
        remove_device(bridge_name)
    except RuntimeError:
        LOG.warning('Failed to remove leftover bridge sink %s', bridge_name)


def wait_for_loopback_gone(loopback_name: str, timeout: float = 2.0, interval: float = 0.05) -> bool:
    '''
    Poll until no pw-loopback with this name is left in PulseAudio.
    Args:
        loopback_name (str): The loopback name to wait for.
        timeout (float): Maximum time to wait in seconds.
        interval (float): Polling interval in seconds.
    Returns:
        bool: True if gone, False if timed out.
    '''
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            playback, capture = _loopback_streams(loopback_name)
            if not playback and not capture:
                return True
        except pulsectl.PulseError:
            pass
        time.sleep(interval)
    return False


def get_loopback_targets(loopback_name: str) -> tuple[str, str] | None:
    '''
    Get the targets a running pw-loopback was created with.
    Loopbacks of older versions, which the session manager linked, recorded none.
    Args:
        loopback_name (str): The loopback name used when creating.
    Returns:
        tuple: (capture target, playback target), or None unless exactly one loopback with this name is running.
    '''
    try:
        playback, capture = _loopback_streams(loopback_name)
    except pulsectl.PulseError:
        return None
    if len(playback) != 1 or len(capture) != 1:
        return None
    return capture[0].proplist.get('pulsemeeter.target', ''), playback[0].proplist.get('pulsemeeter.target', '')


def kill_stray_loopback(loopback_name: str) -> int:
    '''
    Terminate running pw-loopbacks with this name that we hold no process handle for.
    Args:
        loopback_name (str): The loopback name used when creating.
    Returns:
        int: Number of processes signalled.
    '''
    try:
        playback, capture = _loopback_streams(loopback_name)
    except pulsectl.PulseError:
        LOG.error('Failed to look up stray loopbacks for %s', loopback_name)
        return 0

    # pw-loopback sets node.group = "pw-loopback-<pid>"
    pids = set()
    for stream in playback + capture:
        pid = stream.proplist.get('node.group', '').removeprefix('pw-loopback-')
        if pid.isdigit():
            pids.add(int(pid))

    killed = 0
    for pid in pids:
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                argv = f.read().split(b'\0')
            # guard against pid reuse
            if not argv[0].endswith(b'pw-loopback') or loopback_name.encode() not in argv:
                continue
            os.kill(pid, signal.SIGTERM)
            killed += 1
        except OSError:
            continue

    if killed:
        LOG.debug('Terminated %d stray loopback(s) named %s', killed, loopback_name)
    return killed


def list_ports(port_type: str) -> dict[str, list[str]]:
    '''
    Get the ports of every device in PipeWire.
    Args:
        port_type (str): 'input' or 'output'.
    Returns:
        dict[str, list[str]]: port names by device name, in the order pw-link lists them.
    '''
    command = ['pw-link', f'--{port_type}']
    ret, stdout, stderr = run_command(command)
    if ret != 0:
        raise RuntimeError(f"Failed to get ports: {stderr}")

    # pw-link lists ports as 'node_name:port_name', one per line
    # Split on the last colon: node names can contain colons themselves
    # (bluetooth nodes carry the MAC, e.g. 'bluez_output.6C:FB:ED:49:B3:3A')
    ports = {}
    for line in stdout.splitlines():
        node, _, port = line.rpartition(':')
        if node and port:
            ports.setdefault(node, []).append(port)

    return ports


def get_links(node_name: str) -> list[tuple[str, str]]:
    '''
    Get the links leaving a node's output ports.
    Args:
        node_name (str): Name of the node.
    Returns:
        list[tuple[str, str]]: (output port, input port) pairs, both as 'node_name:port_name'.
    '''
    command = ['pw-link', '--links', '--output']
    ret, stdout, stderr = run_command(command)
    if ret != 0:
        raise RuntimeError(f"Failed to get links: {stderr}")

    # Each output port is listed at the start of a line, its links follow it indented as '  |-> node:port'
    links = []
    port = ''
    for line in stdout.splitlines():
        if not line.startswith(' '):
            port = line
        elif port.rpartition(':')[0] == node_name and '|->' in line:
            links.append((port, line.partition('|->')[2].strip()))

    return links


def get_ports(port_type: str, device_name: str) -> list[str]:
    '''
    Get ports for a device in PipeWire.
    Args:
        port_type (str): 'input' or 'output'.
        device_name (str): Name of the device.
    Returns:
        list[str]: list of port names.
    '''
    return list_ports(port_type).get(device_name, [])


def wait_for_ports(port_counts: dict[str, int], timeout: float = 5.0, interval: float = 0.05) -> list[str]:
    '''
    Poll until devices have all their ports in PipeWire.
    Args:
        port_counts (dict[str, int]): The number of ports to wait for in each
            direction, by device name.
        timeout (float): Maximum time to wait in seconds.
        interval (float): Polling interval in seconds.
    Returns:
        list[str]: The devices still missing ports when the time ran out.
    '''
    deadline = time.monotonic() + timeout
    while True:
        try:
            listed = [list_ports('input'), list_ports('output')]
        except RuntimeError:
            listed = [{}, {}]

        missing = [
            name for name, count in port_counts.items()
            if any(len(ports.get(name, [])) < count for ports in listed)
        ]
        if not missing or time.monotonic() >= deadline:
            return missing
        time.sleep(interval)


def mute(device_type: str, device_name: str, state: bool, pulse=None) -> int:
    '''
    Change mute state of a device.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        state (bool): True to mute, False to unmute.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    if pulse is None:
        pulse = PULSE

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    pulse.mute(device, state)
    return True


def set_primary(device_type: str, device_name: str, pulse=None) -> bool:
    '''
    Set a device as primary.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    if pulse is None:
        pulse = PULSE

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    pulse.default_set(device)

    return True


def set_volume(device_type: str, device_name: str, val: int, selected_channels: list[bool] = None) -> bool:
    '''
    Change device volume.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        val (int): Volume value (0-153).
        selected_channels (list): List of booleans indicating which channels to change.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    val = min(max(0, val), 153)

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    # set the volume
    volume_value = device.volume

    # set by channel
    channels = len(device.volume.values)
    volume_list = []

    if selected_channels is None:
        volume_value.value_flat = val / 100
        PULSE.volume_set(device, volume_value)
        return True

    for channel in range(channels):

        # change volume for selected channel
        if selected_channels[channel] is True:
            volume_list.append(val / 100)

        # channels that are not selected don't have their volume changed
        else:
            volume_list.append(device.volume.values[channel])

    volume_value = pulsectl.PulseVolumeInfo(volume_list)

    PULSE.volume_set(device, volume_value)
    return True


def device_exists(device_name: str) -> bool:
    '''
    Check if a device exists by name (sink or source).
    Args:
        device_name (str): The name of the device to check.
    Returns:
        bool: True if the device exists, False otherwise.
    '''
    source_exists = get_device_by_name('source', device_name)
    sink_exists = get_device_by_name('sink', device_name)
    return source_exists is not None or sink_exists is not None


def get_primary(device_type: str, pulse=None) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get the primary device.
    Args:
        device_type (str): 'sink' or 'source'.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        Device object or None.
    '''
    if pulse is None:
        pulse = PULSE

    if device_type == 'sink':
        return pulse.sink_default_get()
    return pulse.source_default_get()


def get_device_by_name(device_type: str, device_name: str) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get a device object by type and name.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
    Returns:
        Device object or None if not found.
    '''
    try:
        if device_type == 'sink':
            return PULSE.get_sink_by_name(device_name)

        return PULSE.get_source_by_name(device_name)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def get_device_by_index(device_type: str, device_index: str) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get a device object by type and name.
    Args:
        device_type (str): 'sink' or 'source'.
        device_index (str): Index of the device on pulse.
    Returns:
        Device object or None if not found.
    '''
    try:
        if device_type == 'sink':
            return PULSE.sink_info(device_index)

        return PULSE.source_info(device_index)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def get_app_device(app_type: str, app: PulseSinkInputInfo | PulseSourceOutputInfo) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get the device an application stream is on.
    Args:
        app_type (str): 'sink_input' (plays into app.sink) or 'source_output' (records from app.source).
        app: The application stream object.
    Returns:
        Device object or None if not found.
    '''
    try:
        if app_type == 'sink_input':
            return PULSE.sink_info(app.sink)

        return PULSE.source_info(app.source)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def app_mute(app_type: str, index: int, state: bool) -> bool:
    '''
    Mute or unmute an application stream by type and index.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
        index (int): Index of the application stream.
        state (bool): True to mute, False to unmute.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    app = app_by_id(index, app_type)
    PULSE.mute(app, state)

    return True


def app_volume(app_type: str, index: int, val: int) -> bool:
    '''
    Set the volume of an application stream by type and index.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
        index (int): Index of the application stream.
        val (int): Volume value (0-153).
    Returns:
        int: 0 on success, -1 on failure.
    '''
    app = app_by_id(index, app_type)
    channels = len(app.volume.values)
    volume = pulsectl.PulseVolumeInfo(val / 100, channels)
    PULSE.volume_set(app, volume)
    return True


def is_hardware_device(device: PulseSinkInfo | PulseSourceInfo) -> bool:
    '''
    Determine if a device is a hardware device (not a monitor or null sink).
    Args:
        device: The device object to check.
    Returns:
        bool: True if hardware, False otherwise.
    '''
    is_easy = 'easyeffects_' in device.name
    is_monitor = device.proplist.get('device.class') == "monitor"
    is_null = device.proplist.get('factory.name') == 'support.null-audio-sink'

    if not is_monitor and (not is_null or is_easy):
        return True

    return False


def list_devices(device_type: str) -> list[PulseSinkInfo | PulseSourceInfo]:
    '''
    List all hardware devices of a given type (sink or source).
    Args:
        device_type (str): 'sink' or 'source'.
    Returns:
        list: List of hardware device objects.
    '''
    pulse = pulsectl.Pulse()
    list_pa_devices = pulse.sink_list if device_type == 'sink' else pulse.source_list
    device_list = []
    for device in list_pa_devices():
        if is_hardware_device(device):
            device_list.append(device)

    return device_list


def app_by_id(index: int, app_type: str) -> PulseSinkInputInfo | PulseSourceOutputInfo:
    '''
    Return a specific app by index and type.
    Args:
        index (int): Index of the application stream.
        app_type (str): 'sink_input' or 'source_output'.
    Returns:
        App object.
    '''
    app_info = PULSE.sink_input_info if app_type == 'sink_input' else PULSE.source_output_info
    app = app_info(index)
    device = get_app_device(app_type, app)
    app.device_name = device.name
    return app


def get_app_object_id(index: int, app_type: str) -> int | None:
    '''Return the app stream's PipeWire object id, or None if not resolvable.'''
    # only the stream's proplist is needed, not its device (app_by_id)
    app_info = PULSE.sink_input_info if app_type == 'sink_input' else PULSE.source_output_info
    try:
        app = app_info(index)
    except pulsectl.PulseError:
        return None
    object_id = app.proplist.get('object.id')
    return int(object_id) if object_id is not None else None


def list_apps(app_type: str) -> list[PulseSinkInputInfo | PulseSourceOutputInfo]:
    '''
    List all application streams of a given type, filtering out pavucontrol and peak sinks.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
    Returns:
        list: List of application stream objects.
    '''
    app_list = []
    full_app_list = PULSE.sink_input_list() if app_type == 'sink_input' else PULSE.source_output_list()

    for app in full_app_list:

        hasname = app.proplist.get('application.name', False)
        is_peak = '_peak' in app.proplist.get('application.name', '')
        is_pavucontrol = app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol'
        is_pm_loopback = 'pm_route_' in app.proplist.get('node.name', '')
        if is_peak or is_pavucontrol or is_pm_loopback or not hasname:
            continue

        app.device_name = get_app_device(app_type, app).name
        app_list.append(app)

    return app_list


def is_pipewire() -> bool:
    '''
    Check if pulseaudio is available on the system.
    Returns:
        bool: True if pulseaudio is available, False otherwise.
    '''
    return shutil.which('pipewire-pulse') is not None


def run_command(command: list[str], split: bool = False, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    If split is True, split the command string into a list.
    If env is given, it replaces the environment the command runs in.
    """
    if split and isinstance(command, str):
        command = command.split()
    LOG.debug('Running command: %s', command)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()
